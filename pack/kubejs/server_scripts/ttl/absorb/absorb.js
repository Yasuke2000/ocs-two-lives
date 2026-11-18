// priority: 70
// Absorption (Sprint 3-4, S5 / WP6): how a unique changes hands between souls in Life 2. The registry (registry.js)
// owns the records, the Legendary ceiling (skills.toml [legendary] max_holders = the Ten Great Demon Lords) and
// transfer(); this file decides WHEN a transfer happens. Every route is a knob in skills.toml [absorb] / [absorb.<route>].
//
//   duel       a duel anywhere in Life 2 (owner 18/11/2026; was the Labyrinth only), consensual: /ttl absorb duel <p> +
//              /ttl absorb accept <p> open a pact; the fatal blow between the two (lethal = false: turned into a defeat, nobody dies) or a real death inside it ends the duel; the
//              loser's Legendary goes to the winner (needs an absorber unique, EP gate, cooldown), Rare/Common are copied.
//   war        a holder who falls in an official war between nations loses their Legendary to the killer (a real death).
//              "At war" comes from TtlNations.atWar(server, keyA, keyB) on the two souls' nations (TtlNations.of; WP4, only when it exists) and from
//              staff flags (/ttl absorb war <a> <b>).
//   bequest    a holder hands a unique on voluntarily: /ttl absorb bequest <p> <skill>, accepted with /ttl absorb accept <p>.
//   awakening  a True Demon Lord / True Hero (Tensura's own flags) may CLAIM a free Legendary (/ttl absorb free|claim) or
//              CHALLENGE a weaker Legendary holder (/ttl absorb challenge <p>): an open pact that the holder cannot refuse.
//   Combat logging: logging out within combat_log_seconds of a hit in a duel, challenge or war counts as a defeat.
//   Damage liability: a duel or challenge started in a public place makes its initiator pay for the blocks it breaks
//   there (absorb/liability.js, skills.toml [absorb.liability]).
//   Inactive holders return their uniques to the pool in registry.js (sweep); eras are era/era.js.
//
// Server persistentData (JSON strings, TtlRegistry.load/store):
//   ttl.absorb.pacts  [{k, a, b, an, bn, st, t, u, skill?, kind?}]  k = duel | challenge | bequest, a = challenger/giver,
//                     b = the other side (UUIDs), st = pending | open, t = made, u = valid until (millis)
//   ttl.absorb.wars   [[uuidA, uuidB]]  war pairs flagged by staff
//   ttl.absorb.souls  {uuid: "true_demon_lord,true_hero"}  awakenings a soul has used, server-side so the claim is once
//                     per SOUL (owner 18/11/2026): neither a Reset Counter rebirth nor a wiped player record refreshes it;
//                     only a staff full reset (/ttl reset, /ttl absorb clear) does
// Player persistentData: ttl.cd.absorb (millis, cooldown until), ttl.combat.until / ttl.combat.with (last hit in a pact or
// war), ttl.absorb.claimed ("true_demon_lord,true_hero": awakenings already used), and test hooks ttl.absorb.epfake and
// ttl.absorb.awakefake.
const TtlAbsorb = {
  KINDS: ['true_demon_lord', 'true_hero'],
  KIND_WORD: { lord: 'true_demon_lord', hero: 'true_hero', true_demon_lord: 'true_demon_lord', true_hero: 'true_hero' },
  api: undefined,

  // ---- configuration (skills.toml [absorb]) ----------------------------------------------------------

  base() {
    return TtlData.skills.absorb || {}
  },

  num(value, fallback) {
    var n = Number(value)
    return value === undefined || value === null || isNaN(n) ? fallback : n
  },

  // The settings of one route: [absorb] keys, overridden by [absorb.<route>].
  route(name) {
    var base = this.base()
    var own = base[name] || {}
    var pick = key => own[key] !== undefined ? own[key] : base[key]
    return {
      name: name,
      enabled: own.enabled !== false,
      requiresAbsorber: own.requires_absorber !== undefined ? !!own.requires_absorber : name === 'duel',
      legendary: own.legendary !== false,
      copies: own.copies !== undefined ? !!own.copies : name === 'duel',
      lethal: !!own.lethal,
      minEp: this.num(pick('min_ep_ratio'), 0.5),
      maxEp: this.num(pick('max_ep_ratio'), 0),
      cooldownHours: this.num(pick('cooldown_hours'), 72),
      legendaryPerKill: this.num(pick('legendary_per_kill'), 1),
      copiesPerKill: this.num(pick('copies_per_kill'), 1),
      dimensions: own.dimensions || [],
      excluded: own.exclude_dimensions || [],
      own: own
    }
  },

  minutes(key, fallback) {
    return this.num(this.base()[key], fallback) * 60000
  },

  seconds(key, fallback) {
    return this.num(this.base()[key], fallback) * 1000
  },

  // ---- Tensura and registry facts --------------------------------------------------------------------

  tensura() {
    if (this.api !== undefined) return this.api
    try {
      this.api = Java.loadClass('io.github.manasmods.tensura.storage.TensuraStorages')
    } catch (e) {
      this.api = null
      console.warn(`[ttl] absorb: Tensura existence storage not available, EP gates read 0 (${e})`)
    }
    return this.api
  },

  // EP of a player; the `ttl.absorb.epfake` test hook replaces it.
  ep(player) {
    var fake = String(player.persistentData.getString('ttl.absorb.epfake'))
    if (fake) return Number(fake)
    var api = this.tensura()
    if (!api) return 0
    try {
      return Number(api.getExistenceFrom(player).getEP())
    } catch (e) {
      return 0
    }
  },

  awakeFlags(player) {
    var fake = String(player.persistentData.getString('ttl.absorb.awakefake'))
    if (fake) return fake.split(',').filter(s => s)
    var api = this.tensura()
    if (!api) return []
    try {
      var ex = api.getExistenceFrom(player)
      var out = []
      if (ex.isTrueDemonLord()) out.push('true_demon_lord')
      if (ex.isTrueHero()) out.push('true_hero')
      return out
    } catch (e) {
      return []
    }
  },

  souls(server) {
    return TtlRegistry.load(server, 'ttl.absorb.souls', {})
  },

  // Used awakenings: the player's own copy and the server's soul record together, so losing either one changes nothing.
  claimed(player) {
    var list = String(player.persistentData.getString('ttl.absorb.claimed')).split(',').filter(s => s)
    try {
      var rec = String(this.souls(player.server)[TtlRegistry.uid(player)] || '').split(',').filter(s => s)
      rec.forEach(k => { if (list.indexOf(k) < 0) list.push(k) })
    } catch (e) {
      console.warn(`[ttl] absorb: could not read the soul record of ${player.username}: ${e}`)
    }
    return list
  },

  markClaimed(player, kind) {
    var list = this.claimed(player)
    if (list.indexOf(kind) < 0) list.push(kind)
    player.persistentData.putString('ttl.absorb.claimed', list.join(','))
    var souls = this.souls(player.server)
    souls[TtlRegistry.uid(player)] = list.join(',')
    TtlRegistry.store(player.server, 'ttl.absorb.souls', souls)
  },

  // Staff full reset only (/ttl reset, /ttl absorb clear): the soul may awaken and claim again.
  forgetClaims(server, player) {
    player.persistentData.remove('ttl.absorb.claimed')
    var souls = this.souls(server)
    var id = TtlRegistry.uid(player)
    if (souls[id] !== undefined) {
      delete souls[id]
      TtlRegistry.store(server, 'ttl.absorb.souls', souls)
    }
  },

  // Awakenings this soul has and has not used yet.
  openKinds(player) {
    var used = this.claimed(player)
    return this.awakeFlags(player).filter(k => used.indexOf(k) < 0)
  },

  held(server, id) {
    return TtlRegistry.heldBy(TtlRegistry.records(server), id)
  },

  legendaryHeld(server, id) {
    return this.held(server, id).filter(s => TtlRegistry.rarityOf(s) === 'legendary')
  },

  isAbsorber(server, player) {
    var want = (this.base().skills || []).map(s => String(s).replace(/^.*:/, ''))
    var have = this.held(server, TtlRegistry.uid(player))
    var live = TtlManas.uniques(player)
    if (live) live.forEach(s => { if (have.indexOf(s) < 0) have.push(s) })
    return have.some(s => want.indexOf(String(s).replace(/^.*:/, '')) >= 0)
  },

  byId(server, id) {
    var found = null
    server.getPlayerList().getPlayers().forEach(p => { if (TtlRegistry.uid(p) === id) found = p })
    return found
  },

  life2(player) {
    return TtlLife.phase(player) === 'life2'
  },

  voice(server, player, text) {
    try {
      TtlCorridor.voice(server, player.username, text)
    } catch (e) {
      console.warn(`[ttl] absorb: could not tell ${player.username}: ${e}`)
    }
  },

  // ---- cooldown and combat tags ----------------------------------------------------------------------

  cooldownLeft(player) {
    var until = Number(String(player.persistentData.getString('ttl.cd.absorb')) || 0)
    return Math.max(0, until - Date.now())
  },

  startCooldown(player, hours) {
    if (hours > 0) player.persistentData.putString('ttl.cd.absorb', String(Date.now() + hours * 3600000))
  },

  tag(a, b) {
    var until = String(Date.now() + this.seconds('combat_log_seconds', 30))
    a.persistentData.putString('ttl.combat.until', until)
    a.persistentData.putString('ttl.combat.with', TtlRegistry.uid(b))
    b.persistentData.putString('ttl.combat.until', until)
    b.persistentData.putString('ttl.combat.with', TtlRegistry.uid(a))
  },

  inCombat(player) {
    return Number(String(player.persistentData.getString('ttl.combat.until')) || 0) > Date.now()
  },

  untag(player) {
    player.persistentData.remove('ttl.combat.until')
    player.persistentData.remove('ttl.combat.with')
  },

  // ---- pacts and wars --------------------------------------------------------------------------------

  pacts(server) {
    return TtlRegistry.load(server, 'ttl.absorb.pacts', [])
  },

  savePacts(server, list) {
    TtlRegistry.store(server, 'ttl.absorb.pacts', list)
  },

  // Pacts still valid (expired ones are dropped on the way).
  live(server) {
    var now = Date.now()
    var all = this.pacts(server)
    var keep = all.filter(p => Number(p.u) > now)
    if (keep.length !== all.length) this.savePacts(server, keep)
    return keep
  },

  addPact(server, pact) {
    var list = this.live(server).filter(p => !(p.k === pact.k && p.a === pact.a && p.b === pact.b))
    list.push(pact)
    this.savePacts(server, list)
  },

  dropPact(server, pact) {
    this.savePacts(server, this.live(server).filter(p => !(p.k === pact.k && p.a === pact.a && p.b === pact.b)))
  },

  // The open pact under which `killerId` beating `victimId` counts: a duel (either way round) or a challenge by the killer.
  openPact(server, killerId, victimId) {
    var found = null
    this.live(server).forEach(p => {
      if (found || p.st !== 'open') return
      if (p.k === 'duel' && ((p.a === killerId && p.b === victimId) || (p.a === victimId && p.b === killerId))) found = p
      if (p.k === 'challenge' && p.a === killerId && p.b === victimId) found = p
    })
    return found
  },

  wars(server) {
    return TtlRegistry.load(server, 'ttl.absorb.wars', [])
  },

  atWar(server, killer, victim) {
    var conf = this.route('war')
    if (!conf.enabled) return false
    if (conf.own.use_nations !== false) {
      try {
        // TtlNations.atWar takes two nation keys (FTB team ids), not players: a soul in no nation is never at official war.
        if (typeof TtlNations !== 'undefined' && TtlNations && typeof TtlNations.atWar === 'function' && typeof TtlNations.of === 'function') {
          var na = TtlNations.of(server, killer)
          var nb = TtlNations.of(server, victim)
          if (na && nb && na.key !== nb.key && TtlNations.atWar(server, na.key, nb.key)) return true
        }
      } catch (e) {
        console.warn(`[ttl] absorb: the nations war check failed: ${e}`)
      }
    }
    if (conf.own.staff_flags !== false) {
      var a = TtlRegistry.uid(killer)
      var b = TtlRegistry.uid(victim)
      return this.wars(server).some(w => (w[0] === a && w[1] === b) || (w[0] === b && w[1] === a))
    }
    return false
  },

  inDimensions(conf, player) {
    var dim = TtlLife.dimensionOf(player)
    if (conf.excluded && conf.excluded.indexOf(dim) >= 0) return false
    if (!conf.dimensions || conf.dimensions.length === 0) return true
    return conf.dimensions.indexOf(dim) >= 0
  },

  // Damage liability of a pact that just opened (absorb/liability.js); '' when it is not in a public place.
  liability(server, pact, a, b) {
    try {
      if (typeof TtlLiability !== 'undefined') return TtlLiability.onOpen(server, pact, a, b)
    } catch (e) {
      console.error(`[ttl] absorb: liability check failed: ${e}`)
    }
    return ''
  },

  // Which route applies when `killer` beats `victim`, or null. opts.anywhere skips the dimension condition (test hook).
  decide(server, killer, victim, opts) {
    var kid = TtlRegistry.uid(killer)
    var vid = TtlRegistry.uid(victim)
    if (kid === vid || !this.life2(killer) || !this.life2(victim)) return null
    var pact = this.openPact(server, kid, vid)
    if (pact) {
      var name = pact.k === 'duel' ? 'duel' : 'awakening'
      var conf = this.route(name)
      if (conf.enabled && ((opts && opts.anywhere) || (this.inDimensions(conf, killer) && this.inDimensions(conf, victim)))) {
        return { route: name, conf: conf, pact: pact }
      }
    }
    if (this.atWar(server, killer, victim)) return { route: 'war', conf: this.route('war'), pact: null }
    return null
  },

  // ---- the absorption itself -------------------------------------------------------------------------

  shuffle(list) {
    for (var i = list.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1))
      var t = list[i]
      list[i] = list[j]
      list[j] = t
    }
    return list
  },

  // A victim as the engine sees it. `offline` (combat log): the record moves at once, the skill leaves them at login.
  subject(victim, offline) {
    return { id: TtlRegistry.uid(victim), name: String(victim.username), ep: this.ep(victim), player: offline ? null : victim }
  },

  // Moves and copies what the route allows from victim `v` to `killer`. Returns {ok, route, why, moved, copied}; nothing is
  // spent (cooldown, pact, awakening) unless something really changed hands.
  resolve(server, killer, v, route, ctx) {
    var conf = this.route(route)
    var out = { ok: false, route: route, why: '', moved: [], copied: [] }
    var fail = why => {
      out.why = why
      return out
    }
    if (!conf.enabled) return fail('the route is off')
    if (!this.life2(killer)) return fail('the killer is not in Life 2')
    if (conf.requiresAbsorber && !this.isAbsorber(server, killer)) return fail('the killer holds no absorbing unique')
    if (this.cooldownLeft(killer) > 0) return fail(`absorb cooldown, ${Math.ceil(this.cooldownLeft(killer) / 3600000)} h left`)
    var kep = this.ep(killer)
    if (conf.minEp > 0 && v.ep < kep * conf.minEp) return fail(`the victim's EP is below ${Math.round(conf.minEp * 100)}% of the killer's`)
    if (conf.maxEp > 0 && v.ep > kep * conf.maxEp) return fail(`the victim's EP is above ${Math.round(conf.maxEp * 100)}% of the killer's`)
    var kid = TtlRegistry.uid(killer)
    var recs = TtlRegistry.records(server)
    var theirs = TtlRegistry.heldBy(recs, v.id)
    var mine = TtlRegistry.heldBy(recs, kid)
    var reason = `${route}: ${v.name} fell to ${killer.username}${ctx && ctx.logout ? ' (combat log)' : ''}`
    if (conf.legendary) {
      var legends = this.shuffle(theirs.filter(s => TtlRegistry.rarityOf(s) === 'legendary' && mine.indexOf(s) < 0))
      if (ctx && ctx.skill) legends = legends.filter(s => s === ctx.skill)
      for (var i = 0; i < legends.length && out.moved.length < conf.legendaryPerKill; i++) {
        if (TtlRegistry.transfer(server, v.player || v.id, killer, legends[i], route, reason)) out.moved.push(legends[i])
      }
    }
    if (conf.copies) {
      var common = this.shuffle(theirs.filter(s => TtlRegistry.rarityOf(s) !== 'legendary' && mine.indexOf(s) < 0))
      if (ctx && ctx.skill) common = common.filter(s => s === ctx.skill)
      for (var j = 0; j < common.length && out.copied.length < conf.copiesPerKill; j++) {
        if (TtlRegistry.available(server, [common[j]], kid).length === 0) continue
        if (TtlRegistry.grant(server, killer, common[j], `${route}: copied from ${v.name}`)) out.copied.push(common[j])
      }
    }
    if (out.moved.length === 0 && out.copied.length === 0) {
      return fail(theirs.length === 0 ? 'the victim holds no unique' : 'nothing could change hands (held already, a cap, or the Legendary ceiling)')
    }
    this.startCooldown(killer, conf.cooldownHours)
    out.ok = true
    var titles = out.moved.concat(out.copied).map(s => TtlCorridor.title(s)).join(', ')
    this.voice(server, killer, `You take ${titles} from ${v.name}.`)
    if (v.player) this.voice(server, v.player, `${killer.username} takes ${titles} from you.`)
    console.info(`[ttl] absorb: ${killer.username} <- ${v.name} by ${route}: moved ${out.moved.join(',') || '-'} copied ${out.copied.join(',') || '-'}`)
    return out
  },

  // A kill or a defeat between two players. `force` (test hook): only when that route is in force. Returns the result.
  onKill(server, killer, victim, force, ctx) {
    var c = ctx || {}
    var d = this.decide(server, killer, victim, c)
    if (!d) return { ok: false, route: '', why: 'no duel, challenge or war between them', moved: [], copied: [] }
    if (force && d.route !== force) return { ok: false, route: d.route, why: `no ${force} in force (${d.route} is)`, moved: [], copied: [] }
    var res = this.resolve(server, killer, this.subject(victim, !!c.logout), d.route, c)
    if (d.pact) {
      this.dropPact(server, d.pact)
      try {
        if (typeof TtlLiability !== 'undefined') TtlLiability.settle(server, TtlLiability.pactKey(d.pact))
      } catch (e) {
        console.error(`[ttl] absorb: settling the duel damage failed: ${e}`)
      }
      if (res.ok && d.route === 'awakening' && d.pact.kind) this.markClaimed(killer, d.pact.kind)
      if (!res.ok) {
        this.voice(server, killer, `The ${d.route} ends without a prize: ${res.why}.`)
        this.voice(server, victim, `The ${d.route} with ${killer.username} ends: you keep what you hold.`)
      }
    }
    this.untag(killer)
    if (!c.logout) this.untag(victim)
    return res
  },

  // A blow between two players (EntityEvents.beforeHurt). Tags both for combat logging while a pact or a war holds. True
  // when the blow would be fatal inside a non-lethal pact: the caller cancels it and the duel is settled here.
  onHit(server, attacker, victim, damage) {
    if (!this.life2(attacker) || !this.life2(victim)) return false
    var d = this.decide(server, attacker, victim, null)
    if (!d) return false
    this.tag(attacker, victim)
    if (d.route === 'war' || d.conf.lethal) return false
    if (!(damage >= Number(victim.getHealth()))) return false
    console.info(`[ttl] absorb: ${attacker.username} wins the ${d.route} against ${victim.username}`)
    this.onKill(server, attacker, victim, null, null)
    return true
  },

  // ---- duel, bequest, awakening: what players ask for ------------------------------------------------

  // Each returns an error text for the player, or null when it went through.
  offerDuel(server, player, other) {
    var conf = this.route('duel')
    if (!conf.enabled) return 'Duels for skills are switched off.'
    if (!this.life2(player) || !this.life2(other)) return 'Only souls in their second life can duel for skills.'
    if (TtlRegistry.uid(player) === TtlRegistry.uid(other)) return 'You cannot duel yourself.'
    var now = Date.now()
    this.addPact(server, { k: 'duel', a: TtlRegistry.uid(player), b: TtlRegistry.uid(other), an: String(player.username), bn: String(other.username), st: 'pending', t: now, u: now + this.minutes('offer_minutes', 5) })
    TtlCorridor.buttons(server, other.username, `${player.username} challenges you to a duel for skills${conf.dimensions.length ? ` in ${conf.dimensions.join(', ')}` : ''}.`, [
      { label: 'Accept', command: `/ttl absorb accept ${player.username}`, color: 'green', hover: 'The loser may lose a unique skill' },
      { label: 'Decline', command: `/ttl absorb decline ${player.username}`, color: 'red', hover: 'Refuse the duel' }
    ])
    this.voice(server, player, `You challenge ${other.username}. They have ${this.num(this.base().offer_minutes, 5)} minutes to accept.`)
    return null
  },

  offerBequest(server, player, other, skill) {
    var conf = this.route('bequest')
    if (!conf.enabled) return 'Bequests are switched off.'
    if (!this.life2(player) || !this.life2(other)) return 'Only souls in their second life can pass on a skill.'
    var id = TtlRegistry.uid(player)
    if (id === TtlRegistry.uid(other)) return 'You cannot bequeath a skill to yourself.'
    if (this.held(server, id).indexOf(skill) < 0) return `You do not hold ${TtlCorridor.title(skill)} through the registry.`
    if (conf.own.legendary_only && TtlRegistry.rarityOf(skill) !== 'legendary') return 'Only Legendary skills can be bequeathed.'
    if (this.inCombat(player)) return 'You cannot bequeath a skill in the middle of a fight.'
    if (this.held(server, TtlRegistry.uid(other)).indexOf(skill) >= 0) return `${other.username} holds ${TtlCorridor.title(skill)} already.`
    var now = Date.now()
    this.addPact(server, { k: 'bequest', a: id, b: TtlRegistry.uid(other), an: String(player.username), bn: String(other.username), st: 'pending', t: now, u: now + this.minutes('offer_minutes', 5), skill: skill })
    TtlCorridor.buttons(server, other.username, `${player.username} wants to bequeath you ${TtlCorridor.title(skill)}.`, [
      { label: 'Accept', command: `/ttl absorb accept ${player.username}`, color: 'green', hover: 'Receive the skill' },
      { label: 'Decline', command: `/ttl absorb decline ${player.username}`, color: 'red', hover: 'Refuse the gift' }
    ])
    this.voice(server, player, `You offer ${TtlCorridor.title(skill)} to ${other.username}. It leaves you when they accept.`)
    return null
  },

  // `/ttl absorb accept <name>` by the one who was asked.
  accept(server, player, name) {
    var id = TtlRegistry.uid(player)
    var want = String(name).toLowerCase()
    var found = null
    this.live(server).forEach(p => {
      if (!found && p.st === 'pending' && p.b === id && String(p.an).toLowerCase() === want) found = p
    })
    if (!found) return `Nobody called ${name} has asked you for anything (or it expired).`
    var other = this.byId(server, found.a)
    if (!other) return `${found.an} is not online.`
    if (found.k === 'duel') {
      var now = Date.now()
      this.dropPact(server, found)
      var open = { k: 'duel', a: found.a, b: found.b, an: found.an, bn: found.bn, st: 'open', t: now, u: now + this.minutes('pact_minutes', 15) }
      this.addPact(server, open)
      var where = this.route('duel').dimensions
      var line = `The duel between ${found.an} and ${found.bn} is on for ${this.num(this.base().pact_minutes, 15)} minutes${where.length ? ` (${where.join(', ')} only)` : ''}. The fatal blow decides it.`
      this.voice(server, player, line)
      this.voice(server, other, line)
      this.liability(server, open, other, player)
      return null
    }
    if (found.k === 'bequest') {
      var ok = TtlRegistry.transfer(server, other, player, found.skill, 'bequest', `${found.an} bequeathed it to ${found.bn}`)
      this.dropPact(server, found)
      if (!ok) {
        this.voice(server, other, 'The bequest could not be completed.')
        return 'The bequest could not be completed (the Legendary ceiling, or you hold it already).'
      }
      this.voice(server, player, `${TtlCorridor.title(found.skill)} is yours, a gift of ${found.an}.`)
      this.voice(server, other, `${TtlCorridor.title(found.skill)} has left you for ${found.bn}.`)
      return null
    }
    return 'Nothing to accept.'
  },

  decline(server, player, name) {
    var id = TtlRegistry.uid(player)
    var want = String(name).toLowerCase()
    var found = null
    this.live(server).forEach(p => {
      if (!found && p.st === 'pending' && p.b === id && String(p.an).toLowerCase() === want) found = p
    })
    if (!found) return `Nobody called ${name} has asked you for anything (or it expired).`
    this.dropPact(server, found)
    var other = this.byId(server, found.a)
    if (other) this.voice(server, other, `${player.username} declines.`)
    return null
  },

  // Legendary uniques an awakened soul could claim right now: skills.toml claim_skills of its open awakenings that the
  // registry has room for (ceiling, per-era slot, cap).
  claimable(server, player) {
    var conf = this.route('awakening')
    var out = []
    if (!conf.enabled || conf.own.claim === false || !TtlRegistry.legendarySlotFree(server)) return out
    var table = conf.own.claim_skills || {}
    var id = TtlRegistry.uid(player)
    this.openKinds(player).forEach(kind => {
      ;(table[kind] || []).forEach(s => {
        var full = `tensura:${s}`
        if (out.some(o => o.skill === full)) return
        if (TtlRegistry.available(server, [full], id, true).length > 0) out.push({ kind: kind, skill: full })
      })
    })
    return out
  },

  claim(server, player, skillPath) {
    var conf = this.route('awakening')
    if (!conf.enabled || conf.own.claim === false) return 'Claiming a Legendary at an awakening is switched off.'
    if (!this.life2(player)) return 'Only a soul in its second life can claim one.'
    var full = `tensura:${String(skillPath).replace(/^.*:/, '')}`
    var table = conf.own.claim_skills || {}
    var kinds = this.openKinds(player).filter(k => (table[k] || []).indexOf(full.replace(/^.*:/, '')) >= 0)
    if (kinds.length === 0) return 'You have no awakening that lets you claim that skill (True Demon Lord or True Hero, once each).'
    if (!TtlRegistry.legendarySlotFree(server)) return 'The Legendary places of this era are taken.'
    var spend = conf.own.spend_slot !== false
    if (!TtlRegistry.grant(server, player, full, `awakening (${kinds[0]}): a free Legendary place`, spend ? { slot: true } : undefined)) {
      return 'The world has no room for that Legendary now (the ceiling of ten, or its holders are complete).'
    }
    this.markClaimed(player, kinds[0])
    this.voice(server, player, `Your awakening is answered. ${TtlCorridor.title(full)} is yours.`)
    try {
      if (!TtlDiscord.isBot(player.username)) TtlDiscord.post(server, `The Voice of the World: ${TtlDiscord.name(player.username)}'s awakening is answered with the Legendary unique skill **${TtlCorridor.title(full)}**.`)
    } catch (e) {
      console.warn(`[ttl] absorb: story line for the claim failed: ${e}`)
    }
    return null
  },

  challenge(server, player, holder) {
    var conf = this.route('awakening')
    if (!conf.enabled || conf.own.challenge === false) return 'Awakening challenges are switched off.'
    if (!this.life2(player) || !this.life2(holder)) return 'Only souls in their second life can challenge.'
    var kinds = this.openKinds(player)
    if (kinds.length === 0) return 'You have no open awakening (True Demon Lord or True Hero, once each).'
    var kid = TtlRegistry.uid(player)
    var hid = TtlRegistry.uid(holder)
    if (kid === hid) return 'You cannot challenge yourself.'
    if (this.legendaryHeld(server, hid).length === 0) return `${holder.username} holds no Legendary skill.`
    var mine = this.ep(player)
    var theirs = this.ep(holder)
    if (conf.maxEp > 0 && theirs > mine * conf.maxEp) return `${holder.username} is stronger than you are: a challenge only reaches a weaker holder.`
    if (conf.minEp > 0 && theirs < mine * conf.minEp) return `${holder.username} is far too weak to be worth a challenge.`
    var busy = this.live(server).some(p => p.k === 'challenge' && p.a === kid)
    if (busy) return 'You have a challenge open already.'
    var now = Date.now()
    var pact = { k: 'challenge', a: kid, b: hid, an: String(player.username), bn: String(holder.username), st: 'open', t: now, u: now + this.minutes('pact_minutes', 15), kind: kinds[0] }
    this.addPact(server, pact)
    var line = `${player.username}, awakened, challenges ${holder.username} for a Legendary skill. It is open for ${this.num(this.base().pact_minutes, 15)} minutes; the fatal blow decides it.`
    this.voice(server, player, line)
    this.voice(server, holder, line)
    this.liability(server, pact, player, holder)
    return null
  },

  // One line per thing a player may want to know (/ttl absorb status).
  status(server, player) {
    var id = TtlRegistry.uid(player)
    var lines = []
    var left = this.cooldownLeft(player)
    lines.push(left > 0 ? `Absorb cooldown: ${Math.ceil(left / 3600000)} h left.` : 'Absorb cooldown: none.')
    lines.push(`Absorber: ${this.isAbsorber(server, player) ? 'yes' : 'no'}. Legendary uniques held: ${this.legendaryHeld(server, id).map(s => TtlCorridor.title(s)).join(', ') || 'none'}.`)
    var kinds = this.openKinds(player)
    if (kinds.length > 0) lines.push(`Open awakenings: ${kinds.join(', ')} (/ttl absorb free, claim, challenge).`)
    this.live(server).forEach(p => {
      if (p.a !== id && p.b !== id) return
      lines.push(`${p.k} ${p.st}: ${p.an} and ${p.bn}${p.skill ? `, ${TtlCorridor.title(p.skill)}` : ''}, ${Math.ceil((Number(p.u) - Date.now()) / 60000)} min left.`)
    })
    return lines
  },

  clear(server, player) {
    var id = TtlRegistry.uid(player)
    this.savePacts(server, this.live(server).filter(p => p.a !== id && p.b !== id))
    ;['ttl.cd.absorb', 'ttl.absorb.epfake', 'ttl.absorb.awakefake'].forEach(k => player.persistentData.remove(k))
    this.forgetClaims(server, player)
    if (typeof TtlLiability !== 'undefined') TtlLiability.cache = null
    this.untag(player)
    this.saveWars(server, this.wars(server).filter(w => w[0] !== id && w[1] !== id))
  },

  saveWars(server, list) {
    TtlRegistry.store(server, 'ttl.absorb.wars', list)
  }
}

// A blow between two players: combat tag, and a fatal blow inside a non-lethal duel or challenge becomes a defeat.
EntityEvents.beforeHurt(event => {
  var defeat = false
  try {
    var victim = event.entity
    if (!victim.isPlayer()) return
    var attacker = event.source.actual
    if (!attacker || !attacker.isPlayer()) return
    defeat = TtlAbsorb.onHit(victim.server, attacker, victim, Number(event.damage))
  } catch (e) {
    console.error(`[ttl] absorb: hit check failed: ${e}`)
  }
  // event.cancel() exits by throwing (KubeJS EventExit): never inside the try above.
  if (defeat) event.cancel()
})

// A real death between players: a duel or challenge with lethal = true, or a war.
EntityEvents.death('minecraft:player', event => {
  try {
    var victim = event.entity
    var killer = event.source.actual
    if (!killer || !killer.isPlayer()) return
    if (TtlLife.phase(victim) !== 'life2') return
    TtlAbsorb.onKill(event.server, killer, victim, null, null)
  } catch (e) {
    console.error(`[ttl] absorb: death check failed: ${e}`)
  }
})

// Combat logging counts as a defeat (skills.toml [absorb] combat_log_seconds).
try {
  PlayerEvents.loggedOut(event => {
    try {
      var player = event.player
      if (!TtlAbsorb.inCombat(player)) return
      var other = TtlAbsorb.byId(event.server, String(player.persistentData.getString('ttl.combat.with')))
      TtlAbsorb.untag(player)
      if (!other) return
      console.info(`[ttl] absorb: ${player.username} logged out in combat with ${other.username}`)
      TtlAbsorb.onKill(event.server, other, player, null, { logout: true })
    } catch (e) {
      console.error(`[ttl] absorb: combat log check failed: ${e}`)
    }
  })
} catch (e) {
  console.warn(`[ttl] absorb: cannot watch logouts, combat logging is not punished (${e})`)
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var op = src => src.hasPermission(2)

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] absorb command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var word = (ctx, name) => String(Arguments.STRING.getResult(ctx, name)).toLowerCase()
  var num = (ctx, name) => Number(Arguments.INTEGER.getResult(ctx, name))
  var player = (ctx, name) => Arguments.PLAYER.getResult(ctx, name)
  var playerArg = name => Commands.argument(name, Arguments.PLAYER.create(event))
  var stringArg = name => Commands.argument(name, Arguments.STRING.create(event))
  var intArg = name => Commands.argument(name, Arguments.INTEGER.create(event))
  var server = ctx => ctx.source.getServer()
  var self = ctx => ctx.source.getPlayerOrException()
  var skillOf = (ctx, name) => `tensura:${word(ctx, name).replace(/^.*:/, '')}`
  var check = (ctx, label, got, want) => {
    if (String(got) !== String(want)) throw `expected ${label} ${want}, got ${got}`
    say(ctx, `absorb: ${label} ${want} as expected`)
    return 1
  }
  var yn = value => value ? 'yes' : 'no'
  // A step for players: an error text goes back to them in red, null means it went through.
  var step = fn => logged(ctx => {
    var me = self(ctx)
    var error = fn(server(ctx), me, ctx)
    if (error) {
      me.tell(Text.red(error))
      return 0
    }
    return 1
  })

  var duel = step((s, me, ctx) => TtlAbsorb.offerDuel(s, me, player(ctx, 'target')))
  var accept = step((s, me, ctx) => TtlAbsorb.accept(s, me, String(Arguments.STRING.getResult(ctx, 'name'))))
  var decline = step((s, me, ctx) => TtlAbsorb.decline(s, me, String(Arguments.STRING.getResult(ctx, 'name'))))
  var bequest = step((s, me, ctx) => TtlAbsorb.offerBequest(s, me, player(ctx, 'target'), skillOf(ctx, 'skill')))
  var claim = step((s, me, ctx) => TtlAbsorb.claim(s, me, word(ctx, 'skill')))
  var challenge = step((s, me, ctx) => TtlAbsorb.challenge(s, me, player(ctx, 'target')))
  var free = logged(ctx => {
    var me = self(ctx)
    var list = TtlAbsorb.claimable(server(ctx), me)
    me.tell(Text.gold(list.length > 0
      ? `Legendary skills your awakening may claim: ${list.map(o => `${TtlCorridor.title(o.skill)} (${o.kind})`).join(', ')}. /ttl absorb claim <skill>`
      : 'No Legendary skill is free for you to claim now.'))
    return 1
  })
  var status = logged(ctx => {
    var me = self(ctx)
    TtlAbsorb.status(server(ctx), me).forEach(line => me.tell(Text.gold(line)))
    return 1
  })

  var simulate = withRoute => logged(ctx => {
    var s = server(ctx)
    var res = TtlAbsorb.onKill(s, player(ctx, 'killer'), player(ctx, 'victim'), withRoute ? word(ctx, 'route') : null, { anywhere: true })
    say(ctx, res.ok
      ? `absorb simulate: ${res.route} moved ${res.moved.join(',') || '-'} copied ${res.copied.join(',') || '-'}`
      : `absorb simulate: refused (${res.why})`)
    return res.ok ? 1 : 0
  })
  var epSet = logged(ctx => {
    player(ctx, 'target').persistentData.putString('ttl.absorb.epfake', String(num(ctx, 'n')))
    say(ctx, `absorb: ${player(ctx, 'target').username} counts as EP ${num(ctx, 'n')} until cleared`)
    return 1
  })
  var war = ctx => {
    var s = server(ctx)
    var a = TtlRegistry.uid(player(ctx, 'a'))
    var b = TtlRegistry.uid(player(ctx, 'b'))
    var list = TtlAbsorb.wars(s).filter(w => !((w[0] === a && w[1] === b) || (w[0] === b && w[1] === a)))
    list.push([a, b])
    TtlAbsorb.saveWars(s, list)
    say(ctx, `absorb: ${player(ctx, 'a').username} and ${player(ctx, 'b').username} are at war (staff flag)`)
    return 1
  }
  var warClear = ctx => {
    TtlAbsorb.saveWars(server(ctx), [])
    say(ctx, 'absorb: staff war flags cleared')
    return 1
  }
  var awake = ctx => {
    var kind = TtlAbsorb.KIND_WORD[word(ctx, 'kind')]
    if (!kind) throw 'kind is lord or hero'
    var target = player(ctx, 'target')
    var list = String(target.persistentData.getString('ttl.absorb.awakefake')).split(',').filter(k => k && k !== kind)
    if (word(ctx, 'state') === 'on') list.push(kind)
    target.persistentData.putString('ttl.absorb.awakefake', list.join(','))
    say(ctx, `absorb: ${target.username} awakened as ${list.join(',') || 'nothing'} (test hook)`)
    return 1
  }
  // Test hook: drop only the player's own copy of the used awakenings, as a Reset Counter that rebuilt the player would.
  var wipeLocal = ctx => {
    player(ctx, 'target').persistentData.remove('ttl.absorb.claimed')
    say(ctx, `absorb: ${player(ctx, 'target').username}'s own awakening record wiped (test hook; the soul record stays)`)
    return 1
  }
  var clearOne = ctx => {
    TtlAbsorb.clear(server(ctx), player(ctx, 'target'))
    say(ctx, `absorb: cleared everything of ${player(ctx, 'target').username}`)
    return 1
  }

  var expectPlayer = field => logged(ctx => {
    var s = server(ctx)
    var p = player(ctx, 'target')
    var data = p.persistentData
    if (field === 'cooldown') return check(ctx, `${p.username} cooldown`, yn(TtlAbsorb.cooldownLeft(p) > 0), word(ctx, 'value'))
    if (field === 'echo') {
      var opts = String(data.getString('ttl.uniqueOptions')).split(',').filter(o => o)
      return check(ctx, `${p.username} Legendary echo offered`, yn(opts.some(o => TtlRegistry.rarityOf(o) === 'legendary')), word(ctx, 'value'))
    }
    if (field === 'options') return check(ctx, `${p.username} unique options`, String(data.getString('ttl.uniqueOptions')).split(',').filter(o => o).length, num(ctx, 'n'))
    if (field === 'kinds') return check(ctx, `${p.username} open awakenings`, TtlAbsorb.openKinds(p).length, num(ctx, 'n'))
    if (field === 'claimable') return check(ctx, `${p.username} claimable Legendaries`, TtlAbsorb.claimable(s, p).length, num(ctx, 'n'))
    if (field === 'absorber') return check(ctx, `${p.username} absorber`, yn(TtlAbsorb.isAbsorber(s, p)), word(ctx, 'value'))
    if (field === 'combat') return check(ctx, `${p.username} in combat`, yn(TtlAbsorb.inCombat(p)), word(ctx, 'value'))
    var kind = TtlAbsorb.KIND_WORD[field]
    return check(ctx, `${p.username} used ${field}`, yn(TtlAbsorb.claimed(p).indexOf(kind) >= 0), word(ctx, 'value'))
  })
  // `ttl absorb expect <player> <field> <value>` (player first, as the tests and sprint3-4.md write it).
  var expectTarget = playerArg('target')
  ;['cooldown', 'echo', 'absorber', 'combat', 'lord', 'hero'].forEach(field => {
    expectTarget = expectTarget.then(Commands.literal(field).then(stringArg('value').executes(expectPlayer(field))))
  })
  ;['options', 'kinds', 'claimable'].forEach(field => {
    expectTarget = expectTarget.then(Commands.literal(field).then(intArg('n').executes(expectPlayer(field))))
  })

  event.register(Commands.literal('ttl')
    .then(Commands.literal('absorb')
      .executes(status)
      .then(Commands.literal('status').executes(status))
      .then(Commands.literal('duel').then(playerArg('target').executes(duel)))
      .then(Commands.literal('accept').then(stringArg('name').executes(accept)))
      .then(Commands.literal('decline').then(stringArg('name').executes(decline)))
      .then(Commands.literal('bequest').then(playerArg('target').then(stringArg('skill').executes(bequest))))
      .then(Commands.literal('free').executes(free))
      .then(Commands.literal('claim').then(stringArg('skill').executes(claim)))
      .then(Commands.literal('challenge').then(playerArg('target').executes(challenge)))
      .then(Commands.literal('simulate').requires(op)
        .then(playerArg('killer').then(playerArg('victim')
          .executes(simulate(false))
          .then(stringArg('route').executes(simulate(true))))))
      .then(Commands.literal('ep').requires(op)
        .then(playerArg('target').then(intArg('n').executes(epSet))))
      .then(Commands.literal('war').requires(op)
        .then(Commands.literal('clear').executes(logged(warClear)))
        .then(playerArg('a').then(playerArg('b').executes(logged(war)))))
      .then(Commands.literal('awake').requires(op)
        .then(playerArg('target').then(stringArg('kind').then(stringArg('state').executes(logged(awake))))))
      .then(Commands.literal('clear').requires(op)
        .then(playerArg('target').executes(clearOne)))
      .then(Commands.literal('testwipe').requires(op)
        .then(playerArg('target').executes(logged(wipeLocal))))
      .then(Commands.literal('expect').requires(op)
        .then(Commands.literal('pacts').then(intArg('n').executes(logged(ctx =>
          check(ctx, 'live pacts', TtlAbsorb.live(server(ctx)).length, num(ctx, 'n'))))))
        .then(Commands.literal('wars').then(intArg('n').executes(logged(ctx =>
          check(ctx, 'staff war flags', TtlAbsorb.wars(server(ctx)).length, num(ctx, 'n'))))))
        .then(expectTarget))))
})
