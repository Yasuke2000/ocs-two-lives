// priority: 69
// The necromancer: the ways in, ranks, the Church's Sense, the Holy Hunt on a soul and the grey licence
// (design/architecture/paths-necro-artificer.md §2.1, §2.2, §2.5, §2.6; WP-N3; owner decisions 18/11/2026, O-N5).
// Data: design/data/necro.toml [points] [entry] [rite] [[rank]] [church] [hunt] [licence] → TtlData.necro.
// Commands: necro/commands.js. The legion (raise, knights, sleep) is necro/legion.js (TtlLegion), the tomb necro/sanctum.js.
//
// WAYS IN (R12: no chapter, Oath or boss gates). A Life 2 soul is a necromancer (rank 1, "Gravebinder") once it has any of:
//   race   its current Tensura race is in [entry] races (the wight and ghoul/vampire lines), checked at login and in the loop
//   skill  it has learned one of [entry] skills (create_greater_undead, mortal_fear): a master of the craft needs no rite
//   rite   `/ttl necro rite` at one of its own Bone Altars with one rite spell known ([rite] spells, Tensura's necromancy
//          magic, or Iron's raise_dead in a spell book or scroll it carries) and [rite] ash soul ash or [rite] dust bone dust.
//          Before the Rite such a soul is an ASPIRANT: its kills drop soul ash and bone dust like a necromancer's
//          (TtlNecro.aspirant, reserved line in legion.js onLoot), otherwise the Rite could never be paid.
// RANKS: rank r holds while the points reach [[rank]] points and its needs_any holds (rank 4, Overlord: Wight King or a
// later form, Vampire or a later form, or Mortal Fear). Points come from the system's own acts (TtlLegion pays them through
// addPoints), at most [points] weekly_cap a week. The rank is recomputed on every change and every loop; a lost need
// (a race reset) drops the soul back a rank, the points stay.
// THE CHURCH'S SENSE: a dark TtlRoads route with extra.sense adds it (the roads listener below), on the canon continent
// only (R11). It decays [church] decay_per_week, one point at a time. sense >= marked_at: Marked (stage ttl.necro.marked, the
// Church's bounty list, Church guards hostile whatever the band, Hinata's wild roll x marked_mult, reputation once).
// sense >= hunt_at: the Holy Hunt on the soul ([hunt] hours): the director's `holy_hunt` is fired with {target}; a stub is
// registered when no other package has one (WP-W9 fills it); Hinata's wild roll x hunt_mult; 120 online minutes without
// dying pay "Unbroken" (title + outcast reputation); a death ends it. A soul still at hunt_at is hunted again rearm_hours
// after the last Hunt ended.
// THE LICENCE (the Keeper, Adalmann's road): rank >= [licence] min_rank, Honored with the Church, zero Sense for clean_days,
// in the Church's region (or near one of its NPCs): `/ttl necro licence` → stage ttl.necro.licensed, the title, the paper
// `ttl:exorcist_licence`. A single dark act on the continent revokes it (Church revoke_rep, the paper is taken, a #story
// line). While licensed: extra Church reputation per grave laid to rest; a dust-only legion is no armed band to the Church.
// Life 1 never: every act needs Life 2; the Mortal dimensions refuse the Rite.
//
// Storage
//   player  ttl.necro         JSON {rank, points, wk (week key), week (points this week), entry {how, at}, born, sense,
//                             senseAt (decay clock), zeroAt (Sense reached 0), marked (epoch), licensed (epoch), revoked,
//                             hunt {at, until, mins, tick, paid}, hunts, lastHunt (end), title}
//           ttl.necro.testplace   byte test hook: the licence's place rule is off
//           ttl.necro.testinside  int test hook: 1 = on the continent, 2 = outside (the Sense rule), absent = TtlWorld
//   server  ttl.necro.marked  JSON {uuid: {n (name), at, sense}} the Church's bounty list (radiant boards read bounties())
//           ttl.necro.first.overlord   epoch of the server's first Overlord (one #story line)
//   stages  ttl.necro.rank1..4 (cumulative), ttl.necro.marked, ttl.necro.hunted, ttl.necro.licensed, ttl.title.unbroken
//   score   ttl.necro (rank, for Easy NPC conditions)
//
// PUBLIC API (other packages call these guarded with typeof; `player` is a ServerPlayer)
//   TtlNecro.rank(player)                      0..4, the stored rank (cheap; legion.js reads it for caps)
//   TtlNecro.addPoints(server, player, n, why) rank points through the weekly cap; returns the points paid (0 below rank 1)
//   TtlNecro.title(player) · entry(player) ('' | race | skill | rite) · aspirant(player) (drops before the Rite)
//   TtlNecro.sense(player) · addSense(server, player, n, why) · marked(player) · hunted(player) · licensed(player)
//   TtlNecro.wildMult(def, player)             bosses/wild.js: Hinata's chance multiplier for this soul
//   TtlNecro.guardsHostile(player, faction)    rep/guards.js: Marked souls (the Church) and armed bands (band_factions)
//   TtlNecro.bounties(server)                  [{uuid, name, at, sense}] the Church's bounty list (WP-W13 boards)
//   TtlNecro.rite(server, player, pay) · licence(server, player) · startHunt(server, player, by) · refresh(server, player)
const TtlNecro = {
  KEY: 'ttl.necro',
  MARKED: 'ttl.necro.marked',
  FIRST: 'ttl.necro.first.overlord',
  TESTPLACE: 'ttl.necro.testplace',
  TESTINSIDE: 'ttl.necro.testinside',
  DAY_MS: 86400000,
  WEEK_MS: 604800000,
  apiObj: undefined,
  ironUtils: undefined,
  cache: {},
  bandCache: {},

  conf() {
    return TtlData.necro || {}
  },

  part(name) {
    return this.conf()[name] || {}
  },

  num(table, key, fallback) {
    var v = Number(table[key])
    return isNaN(v) ? fallback : v
  },

  uid(player) {
    return TtlLife.uuid(player)
  },

  // ---- the record --------------------------------------------------------------------------------------------------

  read(player) {
    var raw = String(player.persistentData.getString(this.KEY) || '')
    var r = {}
    try {
      r = raw ? JSON.parse(raw) : {}
    } catch (e) {
      console.error(`[ttl] necro: ${player.username} ${this.KEY} unreadable, starting over: ${e}`)
    }
    var now = Date.now()
    r.rank = Number(r.rank || 0)
    r.points = Number(r.points || 0)
    r.week = Number(r.week || 0)
    r.sense = Number(r.sense || 0)
    if (!r.born) r.born = now
    if (!r.senseAt) r.senseAt = now
    if (r.zeroAt === undefined) r.zeroAt = r.born
    r.hunts = Number(r.hunts || 0)
    return r
  },

  write(player, r) {
    player.persistentData.putString(this.KEY, JSON.stringify(r))
  },

  weekKey() {
    try {
      if (typeof TtlEcon !== 'undefined' && typeof TtlEcon.weekKey === 'function') return String(TtlEcon.weekKey())
    } catch (e) {
      // the plain week below
    }
    return `w${Math.floor((Date.now() / this.DAY_MS + 3) / 7)}`
  },

  rankDefs() {
    return (this.conf().rank || []).slice().sort((a, b) => Number(a.rank) - Number(b.rank))
  },

  rankDef(n) {
    var list = this.rankDefs()
    for (var i = 0; i < list.length; i++) {
      if (Number(list[i].rank) === Number(n)) return list[i]
    }
    return null
  },

  // ---- Tensura and Iron's (read only) --------------------------------------------------------------------------------

  api() {
    if (this.apiObj !== undefined) return this.apiObj
    try {
      this.apiObj = {
        skills: Java.loadClass('io.github.manasmods.manascore.skill.api.SkillAPI'),
        races: Java.loadClass('io.github.manasmods.manascore.race.api.RaceAPI')
      }
    } catch (e) {
      console.error(`[ttl] necro: ManasCore race/skill API unavailable, the race and skill roads are closed: ${e}`)
      this.apiObj = null
    }
    return this.apiObj
  },

  // The soul's current Tensura race id ('' when unknown).
  race(player) {
    var a = this.api()
    if (!a) return ''
    try {
      var r = a.races.getRaceFrom(player).getRace()
      return r.isPresent() ? String(r.get().getRaceId()) : ''
    } catch (e) {
      console.warn(`[ttl] necro: reading ${player.username}'s race failed: ${e}`)
      return ''
    }
  },

  // Skills and magic the soul really holds: learning (negative mastery) and temporary ones do not count.
  learned(player) {
    var a = this.api()
    if (!a) return []
    var out = []
    try {
      a.skills.getSkillsFrom(player).getLearnedSkills().forEach(i => {
        if (i.getMastery() >= 0 && !i.isTemporarySkill()) out.push(String(i.getSkillId()))
      })
    } catch (e) {
      console.warn(`[ttl] necro: reading ${player.username}'s skills failed: ${e}`)
    }
    return out
  },

  // Iron's rite spells the soul carries: in the equipped spell book (Curios) or in any irons_spellbooks stack it holds,
  // read from the saved stack (data component irons_spellbooks:spell_container lists spell ids).
  ironSpells(server, player) {
    var want = (this.part('rite').iron_spells || []).map(String)
    if (want.length === 0) return []
    var texts = []
    var reg = server.registryAccess()
    var dump = st => {
      try {
        if (!st || st.isEmpty()) return
        var sid = ''
        try {
          sid = String(st.id || '')
        } catch (e) {
          sid = ''
        }
        if (sid && sid !== 'undefined' && sid.indexOf('irons_spellbooks:') !== 0) return
        texts.push(String(st.save(reg)))
      } catch (e) {
        // an unreadable stack holds no spell we can see
      }
    }
    try {
      if (this.ironUtils === undefined) {
        try {
          this.ironUtils = Java.loadClass('io.redspace.ironsspellbooks.api.util.Utils')
        } catch (e) {
          this.ironUtils = null
          console.warn(`[ttl] necro: Iron's Utils unavailable, only carried books and scrolls count: ${e}`)
        }
      }
      if (this.ironUtils) dump(this.ironUtils.getPlayerSpellbookStack(player))
      var inv = player.getInventory()
      for (var i = 0; i < inv.getContainerSize(); i++) dump(inv.getItem(i))
    } catch (e) {
      console.warn(`[ttl] necro: reading ${player.username}'s spell books failed: ${e}`)
    }
    return want.filter(id => texts.some(t => t.indexOf(id) >= 0))
  },

  // The rite spells this soul knows (Tensura learned + Iron's carried).
  riteSpells(server, player) {
    var want = (this.part('rite').spells || []).map(String)
    var have = this.learned(player)
    return want.filter(id => have.indexOf(id) >= 0).concat(this.ironSpells(server, player))
  },

  // 'race' | 'skill' | '' : a way in the soul has without the Rite.
  entryRoad(player) {
    var e = this.part('entry')
    if ((e.races || []).map(String).indexOf(this.race(player)) >= 0) return 'race'
    var have = this.learned(player)
    if ((e.skills || []).some(s => have.indexOf(String(s)) >= 0)) return 'skill'
    return ''
  },

  needsMet(player, def) {
    var need = def.needs_any
    if (!need) return true
    if ((need.races || []).map(String).indexOf(this.race(player)) >= 0) return true
    var have = this.learned(player)
    return (need.skills || []).some(s => have.indexOf(String(s)) >= 0)
  },

  // ---- rank and points -------------------------------------------------------------------------------------------

  rank(player) {
    try {
      return this.read(player).rank
    } catch (e) {
      return 0
    }
  },

  title(player) {
    var d = this.rankDef(this.rank(player))
    return d ? String(d.title) : ''
  },

  entry(player) {
    var r = this.read(player)
    return r.entry ? String(r.entry.how) : ''
  },

  // The rank the record and the soul's race/skills give now.
  rankFor(player, r) {
    if (!r.entry) return 0
    var best = 1
    var self = this
    this.rankDefs().forEach(d => {
      var n = Number(d.rank)
      if (n <= best) return
      if (r.points >= Number(d.points || 0) && self.needsMet(player, d)) best = n
    })
    return best
  },

  // Points stop at [points] weekly_cap a week. Below rank 1 nothing is paid (an aspirant's deeds are not the system's yet).
  addPoints(server, player, n, why) {
    n = Math.round(Number(n) || 0)
    if (n <= 0 || TtlLife.phase(player) !== 'life2') return 0
    var r = this.read(player)
    if (!r.entry) return 0
    var wk = this.weekKey()
    if (r.wk !== wk) {
      r.wk = wk
      r.week = 0
    }
    var cap = this.num(this.part('points'), 'weekly_cap', 60)
    var paid = Math.max(0, Math.min(n, cap - r.week))
    if (paid <= 0) {
      console.info(`[ttl] necro: ${player.username} +${n} points (${why || 'points'}) over the weekly cap ${cap}`)
      return 0
    }
    r.week += paid
    r.points += paid
    this.write(player, r)
    console.info(`[ttl] necro: ${player.username} +${paid} rank points (${why || 'points'}), ${r.points} total, ${r.week}/${cap} this week`)
    this.refresh(server, player, 'points')
    return paid
  },

  setPoints(server, player, n) {
    var r = this.read(player)
    r.points = Math.max(0, Math.round(Number(n) || 0))
    this.write(player, r)
    return this.refresh(server, player, 'ops')
  },

  // Recompute everything a soul's state implies and write the mirrors. Returns the record.
  refresh(server, player, why) {
    if (TtlLife.phase(player) !== 'life2') return this.read(player)
    var r = this.read(player)
    var now = Date.now()
    if (!r.entry) {
      var road = this.entryRoad(player)
      if (road) {
        r.entry = { how: road, at: now }
        this.noteChronicle(server, player, 'necro_rite', { count: 'necro.rites', how: road })
        player.tell(Text.darkPurple(road === 'race'
          ? 'Your body already belongs to the dead: the Bone Altar answers you. You are a Gravebinder. /ttl necro'
          : 'You command the magic of the dead well enough to need no rite. You are a Gravebinder. /ttl necro'))
        console.info(`[ttl] necro: ${player.username} became a necromancer by ${road}`)
      }
    }
    this.decay(r, now)
    var before = r.rank
    r.rank = this.rankFor(player, r)
    this.write(player, r)
    if (r.rank !== before) this.onRank(server, player, r, before, why)
    this.church(server, player, r, now)
    this.sync(server, player, r)
    return r
  },

  onRank(server, player, r, from, why) {
    var to = r.rank
    var d = this.rankDef(to)
    var title = d ? String(d.title) : ''
    this.setRankTitle(player, title)
    r.title = title
    this.write(player, r)
    console.info(`[ttl] necro: ${player.username} rank ${from} -> ${to}${title ? ` (${title})` : ''} [${why || ''}]`)
    if (to < from) {
      player.tell(Text.gray(to > 0 ? `The dead weigh your claim again: you are a ${title} now.` : 'The dead no longer answer you.'))
      return
    }
    if (to === 1) {
      player.tell(Text.darkPurple('Gravebinder. The Bone Altar knows your name; raise your first dead there. /ttl guide paths'))
    } else if (to === 4) {
      var tomb = ''
      try {
        if (typeof TtlSanctum !== 'undefined') {
          var best = TtlSanctum.best(server, this.uid(player))
          if (best && best.name) tomb = String(best.name)
        }
      } catch (e) {
        tomb = ''
      }
      player.tell(Text.gold(`Requirements met. The Overlord rises${tomb ? `: Overlord of ${tomb}` : ''}.`))
      this.noteChronicle(server, player, 'necro_overlord', { count: 'necro.overlords' })
      var data = server.persistentData
      if (!data.contains(this.FIRST) && !this.isBot(player)) {
        data.putLong(this.FIRST, Date.now())
        this.discord(server, 'For the first time in this era, the dead have an Overlord.')
      }
    } else {
      player.tell(Text.darkPurple(`${title}. The dead obey you further (/ttl necro rank).`))
    }
  },

  // The rank title is one entry of the comma-separated ttl.titles (story.js / merit.js pattern); lower ranks give way.
  setRankTitle(player, title) {
    var titles = this.rankDefs().map(d => String(d.title))
    var raw = String(player.persistentData.getString('ttl.titles') || '')
    var list = (raw ? raw.split(',') : []).filter(t => titles.indexOf(t) < 0)
    if (title) list.push(title)
    if (list.length) player.persistentData.putString('ttl.titles', list.join(','))
    else player.persistentData.remove('ttl.titles')
  },

  addTitle(player, title, on) {
    var raw = String(player.persistentData.getString('ttl.titles') || '')
    var list = (raw ? raw.split(',') : []).filter(t => t !== title)
    if (on) list.push(title)
    if (list.length) player.persistentData.putString('ttl.titles', list.join(','))
    else player.persistentData.remove('ttl.titles')
  },

  hasTitle(player, title) {
    return String(player.persistentData.getString('ttl.titles') || '').split(',').indexOf(String(title)) >= 0
  },

  // Stages and the scoreboard mirror.
  sync(server, player, r) {
    var st = player.stages
    var put = (id, on) => {
      if (on && !st.has(id)) st.add(id)
      if (!on && st.has(id)) st.remove(id)
    }
    for (var n = 1; n <= 4; n++) put(`ttl.necro.rank${n}`, r.rank >= n)
    put('ttl.necro.marked', !!r.marked)
    put('ttl.necro.hunted', this.hunting(r, Date.now()))
    put('ttl.necro.licensed', !!r.licensed)
    try {
      if (!server.getScoreboard().getObjective('ttl.necro')) server.runCommandSilent('scoreboard objectives add ttl.necro dummy')
      server.runCommandSilent(`scoreboard players set ${player.username} ttl.necro ${r.rank}`)
    } catch (e) {
      console.warn(`[ttl] necro: scoreboard mirror for ${player.username} failed: ${e}`)
    }
  },

  // ---- the Rite --------------------------------------------------------------------------------------------------

  // pay: 'ash' | 'dust' | '' (whichever the soul can pay, ash first).
  riteRefusal(server, player, pay) {
    if (TtlLife.phase(player) !== 'life2') return 'life2only'
    if (TtlLife.isMortal(TtlLife.dimensionOf(player))) return 'mortal'
    var r = this.read(player)
    if (r.entry) return 'already'
    if (typeof TtlLegion === 'undefined') return 'noaltar'
    if (!TtlLegion.nearAltar(server, player)) return 'noaltar'
    if (this.riteSpells(server, player).length === 0) return 'nospell'
    if (!this.ritePay(server, player, pay)) return 'noreagent'
    return ''
  },

  // {item, n} the soul pays the Rite with, or null.
  ritePay(server, player, pay) {
    var c = this.part('rite')
    var ash = this.num(c, 'ash', 10)
    var dust = this.num(c, 'dust', 0)
    var have = id => TtlCmd.run(server, `clear ${player.username} ${id} 0`)
    if (pay !== 'dust' && have('ttl:soul_ash') >= ash) return { item: 'ttl:soul_ash', n: ash, road: 'ash' }
    if (pay !== 'ash' && dust > 0 && have('ttl:bone_dust') >= dust) return { item: 'ttl:bone_dust', n: dust, road: 'dust' }
    return null
  },

  rite(server, player, pay) {
    var why = this.riteRefusal(server, player, pay)
    if (why) return { ok: false, why: why }
    var p = this.ritePay(server, player, pay)
    var altar = TtlLegion.nearAltar(server, player)
    TtlCmd.run(server, `clear ${player.username} ${p.item} ${p.n}`)
    var r = this.read(player)
    r.entry = { how: 'rite', at: Date.now(), paid: p.road }
    this.write(player, r)
    this.noteChronicle(server, player, 'necro_rite', { count: 'necro.rites', how: 'rite' })
    try {
      TtlCmd.run(server, `execute in ${altar.dim} run particle minecraft:soul ${altar.x + 0.5} ${altar.y + 1.2} ${altar.z + 0.5} 0.4 0.6 0.4 0.03 40`)
      TtlCmd.run(server, `execute in ${altar.dim} run playsound minecraft:entity.wither.ambient block @a ${altar.x} ${altar.y} ${altar.z} 0.6 0.6`)
    } catch (e) {
      // the rite needs no show
    }
    player.tell(Text.darkPurple(`The ${p.road === 'ash' ? 'soul ash' : 'bone dust'} burns black on the altar and something on the other side takes note of you.`))
    console.info(`[ttl] necro: ${player.username} performed the Rite (${p.n} ${p.item})`)
    this.refresh(server, player, 'rite')
    return { ok: true, why: '' }
  },

  // A soul that knows a rite spell but has not entered: its kills drop ash and dust (legion.js onLoot). Cached briefly
  // because loot runs on every kill.
  aspirant(player) {
    try {
      if (!player || !this.part('rite').aspirant_drops || TtlLife.phase(player) !== 'life2') return false
      var r = this.read(player)
      if (r.entry) return false
      var key = this.uid(player)
      var hit = this.cache[key]
      var now = Date.now()
      if (hit && now - hit.t < 30000) return hit.v
      var v = this.riteSpells(player.server, player).length > 0
      this.cache[key] = { t: now, v: v }
      return v
    } catch (e) {
      console.warn(`[ttl] necro: aspirant check failed: ${e}`)
      return false
    }
  },

  // ---- the Church's Sense ----------------------------------------------------------------------------------------

  sense(player) {
    var r = this.read(player)
    this.decay(r, Date.now())
    return r.sense
  },

  // One point every week / decay_per_week; zeroAt = the moment Sense reached 0.
  decay(r, now) {
    var per = this.num(this.part('church'), 'decay_per_week', 5)
    if (!(r.sense > 0) || per <= 0) {
      r.sense = Math.max(0, r.sense)
      r.senseAt = now
      return
    }
    var stepMs = this.WEEK_MS / per
    var steps = Math.floor((now - r.senseAt) / stepMs)
    if (steps <= 0) return
    var dec = Math.min(steps, r.sense)
    r.sense -= dec
    r.senseAt += dec * stepMs
    if (r.sense <= 0) {
      r.sense = 0
      r.zeroAt = r.senseAt
      r.senseAt = now
    }
  },

  addSense(server, player, n, why) {
    var r = this.read(player)
    var now = Date.now()
    this.decay(r, now)
    return this.putSense(server, player, r, r.sense + Math.round(Number(n) || 0), why, now)
  },

  setSense(server, player, n, why) {
    var r = this.read(player)
    var now = Date.now()
    this.decay(r, now)
    return this.putSense(server, player, r, Math.round(Number(n) || 0), why, now)
  },

  putSense(server, player, r, n, why, now) {
    var max = this.num(this.part('church'), 'max_sense', 100)
    var was = r.sense
    r.sense = Math.max(0, Math.min(max, n))
    r.senseAt = now
    if (r.sense > 0) r.zeroAt = 0
    else if (was > 0 || !r.zeroAt) r.zeroAt = now
    this.write(player, r)
    console.info(`[ttl] necro: ${player.username} Church Sense ${was} -> ${r.sense} (${why || 'sense'})`)
    this.refresh(server, player, why || 'sense')
    return r.sense
  },

  marked(player) {
    return !!this.read(player).marked
  },

  hunting(r, now) {
    return !!(r.hunt && Number(r.hunt.until) > (now || Date.now()))
  },

  hunted(player) {
    return this.hunting(this.read(player), Date.now())
  },

  licensed(player) {
    return !!this.read(player).licensed
  },

  // Marks and the Hunt follow the Sense. r is decayed and written by the caller (refresh).
  church(server, player, r, now) {
    var c = this.part('church')
    var want = r.sense >= this.num(c, 'marked_at', 20)
    var changed = false
    if (want && !r.marked) {
      r.marked = now
      changed = true
      this.rep(server, player, String(c.faction || 'holy_church'), this.num(c, 'marked_rep', 0), 'marked by the Church')
      this.bounty(server, player, r, true)
      player.tell(Text.red('The Holy Church has marked you. Its guards know your face, its hunters your name.'))
      console.info(`[ttl] necro: ${player.username} is Marked (Sense ${r.sense})`)
    } else if (!want && r.marked) {
      r.marked = 0
      changed = true
      this.bounty(server, player, r, false)
      player.tell(Text.gray("The Church's eye has moved on from you, for now."))
      console.info(`[ttl] necro: ${player.username} is no longer Marked (Sense ${r.sense})`)
    } else if (want) {
      this.bounty(server, player, r, true)
    }
    if (r.hunt && Number(r.hunt.until) <= now) {
      this.endHunt(server, player, r, 'over')
      changed = true
    }
    var h = this.part('hunt')
    var rearm = this.num(h, 'rearm_hours', 72) * 3600000
    if (r.sense >= this.num(c, 'hunt_at', 50) && !r.hunt && (!r.lastHunt || now - Number(r.lastHunt) >= rearm)) {
      this.beginHunt(server, player, r, 'sense', now)
      changed = true
    }
    if (changed) this.write(player, r)
  },

  rep(server, player, f, n, why) {
    if (!n) return null
    try {
      if (typeof TtlRep !== 'undefined') return TtlRep.add(server, player, f, n, why)
    } catch (e) {
      console.error(`[ttl] necro: rep ${f} for ${player.username} failed: ${e}`)
    }
    return null
  },

  // The Church's bounty list: one row per Marked soul (no coins of ours: the radiant boards of WP-W13 read bounties()).
  bounty(server, player, r, on) {
    var data = server.persistentData
    var all = {}
    try {
      all = JSON.parse(String(data.getString(this.MARKED)) || '{}')
    } catch (e) {
      all = {}
    }
    var u = this.uid(player)
    if (on) all[u] = { n: String(player.username), at: Number(all[u] ? all[u].at : r.marked) || Date.now(), sense: r.sense }
    else delete all[u]
    data.putString(this.MARKED, JSON.stringify(all))
  },

  bounties(server) {
    var all = {}
    try {
      all = JSON.parse(String(server.persistentData.getString(this.MARKED)) || '{}')
    } catch (e) {
      all = {}
    }
    return Object.keys(all).map(u => ({ uuid: u, name: all[u].n, at: all[u].at, sense: all[u].sense })).sort((a, b) => b.sense - a.sense)
  },

  // ---- the Holy Hunt on a soul -----------------------------------------------------------------------------------

  startHunt(server, player, by) {
    var r = this.read(player)
    var now = Date.now()
    this.decay(r, now)
    if (this.hunting(r, now)) return false
    this.beginHunt(server, player, r, by || 'ops', now)
    this.write(player, r)
    this.sync(server, player, r)
    return true
  },

  beginHunt(server, player, r, by, now) {
    var h = this.part('hunt')
    var c = this.part('church')
    var name = String(player.username)
    r.hunt = { at: now, until: now + this.num(h, 'hours', 24) * 3600000, mins: 0, tick: now, paid: 0 }
    this.rep(server, player, String(c.faction || 'holy_church'), this.num(h, 'rep', 0), 'the Holy Hunt')
    this.noteChronicle(server, player, 'necro_hunt', { count: 'necro.hunts' })
    var fired = this.fireDirector(server, name)
    var line = String(h.announce || 'The Holy Church has named {soul} an abomination.').replace('{soul}', name)
    if (fired.stub) {
      server.getPlayerList().getPlayers().forEach(p => {
        try {
          if (TtlLife.phase(p) === 'life2') p.tell(Text.red(line))
        } catch (e) {
          // a soul that cannot be told
        }
      })
      if (h.discord !== false && !this.isBot(player)) this.discord(server, line)
    }
    player.tell(Text.red(`The Hunt is on you for ${this.num(h, 'hours', 24)} hours. Stay alive ${this.num(h, 'survive_minutes', 120)} minutes in the world and the Church will remember you as ${h.survive_title || 'Unbroken'}.`))
    console.info(`[ttl] necro: the Holy Hunt is on ${name} (${by}; director ${fired.director ? 'fired' : 'stub'})`)
  },

  // The director's holy_hunt (WP-W9) with {target}; returns {director, stub} (stub: we announce ourselves).
  fireDirector(server, name) {
    var id = String(this.part('hunt').event || 'holy_hunt')
    var out = { director: false, stub: true }
    try {
      if (typeof TtlEvents === 'undefined' || !TtlEvents.get(id)) return out
      var res = TtlEvents.fire(server, id, { vars: { target: name, soul: name, by: 'necro' } })
      out.director = !!(res && res.ok)
      out.stub = !out.director || !!(res.ctx && res.ctx.data && res.ctx.data.stub)
      if (!out.director) console.info(`[ttl] necro: director ${id} for ${name} not started: ${res ? res.error : 'no answer'}`)
    } catch (e) {
      console.error(`[ttl] necro: firing ${id} for ${name} failed: ${e}`)
    }
    return out
  },

  endHunt(server, player, r, why) {
    if (!r.hunt) return
    r.lastHunt = Date.now()
    r.hunts = Number(r.hunts || 0) + 1
    var paid = !!r.hunt.paid
    r.hunt = null
    if (why === 'caught') player.tell(Text.red('The Church caught up with you. The Hunt is over; the Church calls it justice.'))
    else player.tell(Text.gray(paid ? 'The Hunt is over. You were not broken.' : 'The Hunt is over.'))
    console.info(`[ttl] necro: the Holy Hunt on ${player.username} ended (${why})`)
  },

  // Online minutes during the Hunt; at survive_minutes the soul is Unbroken (once per Hunt).
  huntTick(server, player, r, now) {
    if (!this.hunting(r, now)) return false
    var step = Math.max(0, Math.min(now - Number(r.hunt.tick || now), 2 * this.num(this.part('church'), 'loop_seconds', 60) * 1000))
    r.hunt.tick = now
    r.hunt.mins = Number(r.hunt.mins || 0) + step / 60000
    this.checkUnbroken(server, player, r)
    return true
  },

  checkUnbroken(server, player, r) {
    var h = this.part('hunt')
    if (!r.hunt || r.hunt.paid || r.hunt.mins < this.num(h, 'survive_minutes', 120)) return
    r.hunt.paid = Date.now()
    var title = String(h.survive_title || 'Unbroken')
    var rep = h.survive_rep || {}
    var self = this
    Object.keys(rep).forEach(f => self.rep(server, player, f, Number(rep[f]), 'survived the Holy Hunt'))
    this.addTitle(player, title, true)
    if (!player.stages.has('ttl.title.unbroken')) player.stages.add('ttl.title.unbroken')
    player.tell(Text.gold(`You outlasted the Church's Hunt. The dark remembers you as ${title}.`))
    console.info(`[ttl] necro: ${player.username} survived the Hunt (${title})`)
  },

  onDeath(server, player) {
    var r = this.read(player)
    if (!this.hunting(r, Date.now())) return
    this.endHunt(server, player, r, 'caught')
    this.write(player, r)
    this.sync(server, player, r)
  },

  // ---- the licence (the Keeper) ----------------------------------------------------------------------------------

  cleanDays(r, now) {
    if (r.sense > 0 || !r.zeroAt) return 0
    return (now - Number(r.zeroAt)) / this.DAY_MS
  },

  // Where the Church grants it: its canon region, or near one of its NPCs.
  atChurch(server, player) {
    var li = this.part('licence')
    if (String(li.place || 'region') === 'anywhere' || player.persistentData.getBoolean(this.TESTPLACE)) return true
    var f = String(this.part('church').faction || 'holy_church')
    try {
      if (TtlLife.dimensionOf(player) === TtlLife.OVERWORLD && typeof TtlRep !== 'undefined') {
        var fac = TtlRep.factionAt(player.getX(), player.getZ())
        if (fac && String(fac.id) === f) return true
      }
      var def = typeof TtlRep !== 'undefined' ? TtlRep.faction(f) : null
      var r = this.num(li, 'npc_radius', 8)
      var tags = def ? (def.npc_tags || []).map(String) : []
      var near = false
      player.level.getEntitiesWithin(player.boundingBox.inflate(r)).forEach(e => {
        if (near || e.isPlayer()) return
        var et = e.getTags()
        tags.forEach(t => { if (et.contains(t)) near = true })
      })
      return near
    } catch (e) {
      console.warn(`[ttl] necro: the licence place check for ${player.username} failed: ${e}`)
      return false
    }
  },

  licenceRefusal(server, player) {
    if (TtlLife.phase(player) !== 'life2') return 'life2only'
    var li = this.part('licence')
    var c = this.part('church')
    var r = this.read(player)
    var now = Date.now()
    this.decay(r, now)
    if (r.licensed) return 'licensed'
    if (r.rank < this.num(li, 'min_rank', 1)) return 'norank'
    if (r.sense > 0) return 'sense'
    if (this.cleanDays(r, now) < this.num(li, 'clean_days', 14)) return 'clean'
    if (typeof TtlRep === 'undefined' || !TtlRep.atLeast(player, String(c.faction || 'holy_church'), String(li.band || 'honored'))) return 'band'
    if (!this.atChurch(server, player)) return 'place'
    return ''
  },

  licence(server, player) {
    var why = this.licenceRefusal(server, player)
    if (why) return { ok: false, why: why }
    var li = this.part('licence')
    var r = this.read(player)
    r.licensed = Date.now()
    this.write(player, r)
    this.addTitle(player, String(li.title || 'Licensed Exorcist'), true)
    this.rep(server, player, String(this.part('church').faction || 'holy_church'), this.num(li, 'grant_rep', 0), 'the exorcist licence')
    if (li.item) TtlCmd.run(server, `give ${player.username} ${li.item} 1`)
    this.noteChronicle(server, player, 'necro_licence', { count: 'necro.licences' })
    player.tell(Text.aqua('The Church seals your licence. Adalmann was a saint of this Church before it sent him to die; he keeps the dead of the Labyrinth for Rimuru now. Keep yours as he does: raise the fallen of battle, lay the restless to rest, never take a soul. (our interpretation)'))
    console.info(`[ttl] necro: ${player.username} is a Licensed Exorcist`)
    this.refresh(server, player, 'licence')
    return { ok: true, why: '' }
  },

  revoke(server, player, r, why) {
    var li = this.part('licence')
    r.licensed = 0
    r.revoked = Date.now()
    this.write(player, r)
    this.addTitle(player, String(li.title || 'Licensed Exorcist'), false)
    this.rep(server, player, String(this.part('church').faction || 'holy_church'), this.num(li, 'revoke_rep', -20), `licence revoked (${why})`)
    if (li.item) TtlCmd.run(server, `clear ${player.username} ${li.item}`)
    player.tell(Text.red('The Church has torn up your licence. It will not forget why.'))
    if (!this.isBot(player)) this.discord(server, 'The Holy Church has torn up an exorcist\'s licence.')
    console.info(`[ttl] necro: ${player.username}'s licence revoked (${why})`)
  },

  // ---- the roads listener: Sense, revocation, the Keeper's bonus ---------------------------------------------------

  onContinent(player) {
    var t = Number(player.persistentData.getInt(this.TESTINSIDE))
    if (t === 1) return true
    if (t === 2) return false
    var dim = TtlLife.dimensionOf(player)
    if (TtlLife.isMortal(dim)) return false
    try {
      if (typeof TtlWorld !== 'undefined' && typeof TtlWorld.onContinent === 'function') return !!TtlWorld.onContinent(dim, player.getX(), player.getZ())
    } catch (e) {
      console.warn(`[ttl] necro: continent check failed, the Church sees it: ${e}`)
    }
    return true
  },

  onRoad(server, player, res, route) {
    if (!res || !res.ok) return
    var id = String(res.id)
    var extra = (route && route.extra) || {}
    var sense = Math.round(Number(extra.sense || 0))
    var necro = id.indexOf('necro.') === 0
    if (res.road === 'dark' && (sense > 0 || necro)) {
      if (!this.onContinent(player)) {
        console.info(`[ttl] necro: ${player.username} ${id} dark outside the continent: the Church does not see it`)
        return
      }
      var r = this.read(player)
      if (r.licensed) this.revoke(server, player, r, id)
      if (sense > 0) this.addSense(server, player, sense, id)
      return
    }
    if (id === 'necro.rest' && res.road === 'good' && this.licensed(player) && this.onContinent(player)) {
      this.rep(server, player, String(this.part('church').faction || 'holy_church'), this.num(this.part('licence'), 'rest_rep', 0), 'a licensed rest')
    }
  },

  // ---- hooks for other packages -------------------------------------------------------------------------------------

  // bosses/wild.js chanceFor: the Church's hunters roll more often near a Marked or Hunted soul.
  wildMult(def, player) {
    var c = this.part('church')
    if ((c.hunter_bosses || []).map(String).indexOf(String(def.id)) < 0) return 1
    var r = this.read(player)
    if (this.hunting(r, Date.now())) return this.num(c, 'hunt_mult', 5)
    if (r.marked) return this.num(c, 'marked_mult', 3)
    return 1
  },

  // rep/guards.js pulse: guards of `f` turn on this soul although its band would not make them. Cached 5 s.
  guardsHostile(player, f) {
    f = String(f)
    if (TtlLife.phase(player) !== 'life2') return false
    var c = this.part('church')
    var church = String(c.faction || 'holy_church')
    if (f === church && player.stages.has('ttl.necro.marked')) return true
    if ((c.band_factions || []).map(String).indexOf(f) < 0 || typeof TtlLegion === 'undefined') return false
    var key = `${this.uid(player)}|${f}`
    var now = Date.now()
    var hit = this.bandCache[key]
    if (hit && now - hit.t < 5000) return hit.v
    var v = this.armedBand(player, f, church)
    this.bandCache[key] = { t: now, v: v }
    return v
  },

  armedBand(player, f, church) {
    try {
      if (TtlLife.dimensionOf(player) !== TtlLife.OVERWORLD || typeof TtlRep === 'undefined') return false
      var fac = TtlRep.factionAt(player.getX(), player.getZ())
      if (!fac || String(fac.id) !== f) return false
      var c = this.part('church')
      var uuid = this.uid(player)
      var near = TtlLegion.near(uuid, player, this.num(c, 'band_radius', 48))
      if (f === church && this.licensed(player)) {
        var rec = TtlLegion.record(player.server, uuid)
        var dark = {}
        rec.list.forEach(x => { if (x.road === 'ash') dark[`ttl.lid.${x.id}`] = true })
        near = near.filter(e => {
          var hitDark = false
          e.getTags().forEach(t => { if (dark[String(t)]) hitDark = true })
          return hitDark
        })
      }
      return near.length >= this.num(c, 'band_min', 3)
    } catch (e) {
      console.warn(`[ttl] necro: armed band check for ${player.username} failed: ${e}`)
      return false
    }
  },

  // ---- helpers ---------------------------------------------------------------------------------------------------------

  isBot(player) {
    try {
      if (typeof TtlDiscord !== 'undefined' && typeof TtlDiscord.isBot === 'function') return !!TtlDiscord.isBot(player)
    } catch (e) {
      // fall through to the name rule
    }
    return /^TtlBot/.test(String(player.username))
  },

  discord(server, line) {
    try {
      if (typeof TtlDiscord !== 'undefined') TtlDiscord.post(server, line)
    } catch (e) {
      console.warn(`[ttl] necro: Discord line failed: ${e}`)
    }
  },

  noteChronicle(server, player, kind, data) {
    try {
      if (typeof TtlChronicle !== 'undefined' && typeof TtlChronicle.note === 'function') TtlChronicle.note(server, kind, player, data)
    } catch (e) {
      console.error(`[ttl] necro: chronicle note ${kind} failed: ${e}`)
    }
  },

  clear(server, player) {
    var data = player.persistentData
    data.remove(this.KEY)
    data.remove(this.TESTPLACE)
    data.remove(this.TESTINSIDE)
    var self = this
    var titles = this.rankDefs().map(d => String(d.title)).concat([String(this.part('licence').title || ''), String(this.part('hunt').survive_title || '')])
    titles.forEach(t => { if (t) self.addTitle(player, t, false) })
    ;['ttl.necro.rank1', 'ttl.necro.rank2', 'ttl.necro.rank3', 'ttl.necro.rank4', 'ttl.necro.marked', 'ttl.necro.hunted', 'ttl.necro.licensed', 'ttl.title.unbroken'].forEach(s => {
      if (player.stages.has(s)) player.stages.remove(s)
    })
    this.bounty(server, player, { sense: 0 }, false)
    delete this.cache[this.uid(player)]
    this.bandCache = {}
    server.runCommandSilent(`scoreboard players reset ${player.username} ttl.necro`)
  },

  // ---- what a player reads -----------------------------------------------------------------------------------------

  eye(r, now) {
    if (this.hunting(r, now)) return 'Hunted: the Holy Hunt is on you'
    if (r.marked) return 'Marked: the Church has put a bounty on you'
    if (r.sense >= Math.ceil(this.num(this.part('church'), 'marked_at', 20) / 2)) return 'Watched: the Church has heard of you'
    if (r.sense > 0) return 'Noticed: a rumour in the Church'
    return 'Unnoticed'
  },

  lines(server, player) {
    var r = this.refresh(server, player, 'status')
    var now = Date.now()
    var out = []
    if (!r.entry) {
      out.push('You are not a necromancer.')
      out.push(this.riteSpells(server, player).length > 0
        ? `You know the magic of the dead: perform the Rite at your Bone Altar (/ttl necro rite) with ${this.num(this.part('rite'), 'ash', 10)} soul ash${this.num(this.part('rite'), 'dust', 0) > 0 ? ` or ${this.num(this.part('rite'), 'dust', 0)} bone dust` : ''}. Until then your kills already leave ash and dust.`
        : 'Learn a spell of the dead (Create Lesser Undead from a tome or the Spellbinding Table, or Iron\'s Raise Dead), then perform the Rite at a Bone Altar. Wights and ghouls need no rite.')
    } else {
      var next = this.rankDef(r.rank + 1)
      out.push(`${this.title(player)} (rank ${r.rank}), ${r.points} rank points, ${r.wk === this.weekKey() ? r.week : 0}/${this.num(this.part('points'), 'weekly_cap', 60)} this week. Way in: ${r.entry.how}.`)
      if (next) out.push(`Next: ${next.title} at ${next.points} points${next.needs_any ? ' and Wight King, Vampire or Mortal Fear' : ''}.`)
    }
    out.push(`The Church's eye: ${this.eye(r, now)}.`)
    if (this.hunting(r, now)) out.push(`The Hunt ends in ${Math.ceil((Number(r.hunt.until) - now) / 3600000)} h; ${Math.floor(r.hunt.mins)}/${this.num(this.part('hunt'), 'survive_minutes', 120)} minutes outlasted.`)
    if (r.licensed) out.push('You hold the Church\'s licence: a Licensed Exorcist. One dark act and it is gone.')
    else if (r.entry) out.push(`The licence: Honored with the Church and ${this.num(this.part('licence'), 'clean_days', 14)} days without the Church's notice (${Math.floor(this.cleanDays(r, now))} so far). /ttl necro licence in the Church's lands.`)
    return out
  },

  ladder(player) {
    var r = this.read(player)
    return this.rankDefs().map(d => `${Number(d.rank) <= r.rank ? '*' : '-'} ${d.rank} ${d.title}: ${Number(d.rank) === 1 ? 'the Rite, a wight/ghoul race or a master\'s spell' : `${d.points} points`}${d.needs_any ? ' + Wight King, Vampire or Mortal Fear' : ''}`)
  },

  // The refusal a player reads.
  why(code) {
    var t = {
      life2only: 'Only a soul in its second life can walk with the dead.',
      mortal: 'The dead do not answer in the Mortal Realm.',
      already: 'You already walk with the dead (/ttl necro).',
      noaltar: 'Stand at one of your own Bone Altars (bone blocks, a candle, rotten flesh, cobbled deepslate).',
      nospell: 'You need a spell of the dead first: Create Lesser Undead (a tome or the Spellbinding Table) or Iron\'s Raise Dead.',
      noreagent: `The Rite takes ${this.num(this.part('rite'), 'ash', 10)} soul ash${this.num(this.part('rite'), 'dust', 0) > 0 ? ` or ${this.num(this.part('rite'), 'dust', 0)} bone dust` : ''}.`,
      licensed: 'You already hold the licence.',
      norank: 'The licence is for necromancers.',
      sense: 'The Church still senses your dark deeds.',
      clean: `The Church wants ${this.num(this.part('licence'), 'clean_days', 14)} days without a dark deed from you.`,
      band: `The Church must hold you ${String(this.part('licence').band || 'honored')} first.`,
      place: 'Ask in the Church\'s own lands (Lubelius) or of one of its priests.'
    }
    return t[code] || String(code)
  }
}

// The roads listener (priority 69 loads after roads.js; a second try at server load covers any order).
const TtlNecroRoads = {
  done: false,
  hook(late) {
    if (this.done) return
    try {
      if (typeof TtlRoads === 'undefined') {
        if (late) console.warn('[ttl] necro: TtlRoads is not loaded, dark deeds will not reach the Church')
        return
      }
      TtlRoads.listen((server, player, res, route) => TtlNecro.onRoad(server, player, res, route))
      this.done = true
    } catch (e) {
      console.error(`[ttl] necro: listening to the roads failed: ${e}`)
    }
  }
}
TtlNecroRoads.hook(false)

PlayerEvents.loggedIn(event => {
  try {
    if (TtlLife.phase(event.player) === 'life2') TtlNecro.refresh(event.server, event.player, 'login')
  } catch (e) {
    console.error(`[ttl] necro: login refresh of ${event.player.username} failed: ${e}`)
  }
})

EntityEvents.death(event => {
  try {
    var e = event.entity
    if (!e || !e.isPlayer()) return
    TtlNecro.onDeath(event.server, e)
  } catch (err) {
    console.error(`[ttl] necro: death hook failed: ${err}`)
  }
})

ServerEvents.loaded(event => {
  var server = event.server
  TtlNecroRoads.hook(true)
  // WP-W9 owns the director's holy_hunt; until it exists the Hunt fires a stub so the hook is real.
  try {
    var id = String(TtlNecro.part('hunt').event || 'holy_hunt')
    if (typeof TtlEvents !== 'undefined' && !TtlEvents.get(id)) {
      TtlEvents.register({
        id: id,
        label: 'The Holy Hunt',
        start(srv, ctx) {
          return { player: String((ctx.vars || {}).target || ''), stub: true }
        }
      })
    }
  } catch (e) {
    console.error(`[ttl] necro: registering the holy_hunt stub failed: ${e}`)
  }
  var stamp = String(Date.now())
  server.persistentData.putString('ttl.necro.loop', stamp)
  var alive = () => String(server.persistentData.getString('ttl.necro.loop')) === stamp
  var ticks = Math.max(20, TtlNecro.num(TtlNecro.part('church'), 'loop_seconds', 60) * 20)
  var loop = () => server.scheduleInTicks(ticks, () => {
    if (!alive()) return
    var now = Date.now()
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        if (TtlLife.phase(p) !== 'life2') return
        var r = TtlNecro.refresh(server, p, 'loop')
        if (TtlNecro.huntTick(server, p, r, now)) TtlNecro.write(p, r)
      } catch (e) {
        console.error(`[ttl] necro: loop for ${p.username} failed: ${e}`)
      }
    })
    loop()
  })
  loop()
})
