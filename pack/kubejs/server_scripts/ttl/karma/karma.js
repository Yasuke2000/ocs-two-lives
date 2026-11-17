// priority: 88
// Karma v1: what a player did in Life 1 decides their rebirth tier. Every knob is in design/data/karma.toml
// (→ TtlData.karma); the formula is described at the top of that file.
// Deeds are vanilla statistics read through scoreboard objectives with stat criteria (`ttl.s.<key>`): the game
// fills those itself, and EntityEvents.death does not fire for mob deaths here. A few values the stats lack
// (distance, Nether/End visits, advancements) are tracked by tracking.js in player persistentData.
// Life 1 start (join.js, /ttl reset) snapshots the objectives into `ttl.karma.base`; the Life 1 death
// (death.js) stores the difference and the verdict in `ttl.karma.life1` (JSON) plus `ttl.karma.<axis>`,
// `ttl.karma.score`, `ttl.karma.dark`, `ttl.tier`, `ttl.l1.days`, and the stage `ttl.tier.<id>`. Karma
// survives the rebirth (the Corridor never clears these keys); only /ttl reset starts it over.
const TtlKarma = {
  OBJ: 'ttl.s.',
  KILL: 'kill.',
  // Tracked stats → their persistentData key (reset at Life 1 start, so they need no snapshot).
  TRACKED: { far: 'ttl.l1.far', nether: 'ttl.l1.nether', end: 'ttl.l1.end', advancements: 'ttl.l1.adv' },
  KEYS: ['ttl.karma.base', 'ttl.karma.life1', 'ttl.karma.score', 'ttl.karma.dark', 'ttl.karma.bonus', 'ttl.tier', 'ttl.l1.days'],

  conf() {
    return TtlData.karma
  },

  // Every stat as {key, criterion | track, axis, weight, per, group, label, format, major}; the kinds of foe
  // are added as `kill.<path>` stats without an axis (they score through their kind count).
  stats() {
    var conf = this.conf()
    var out = conf.stats.slice()
    var kill = this.KILL
    // Stat criteria write the entity id with a dot: minecraft.killed:minecraft.zombie.
    conf.hostiles.ids.forEach(id => out.push({ key: kill + String(id).replace(/^.*:/, ''), criterion: `minecraft.killed:${String(id).replace(':', '.')}`, kind: true }))
    return out
  },

  stat(key) {
    var all = this.stats()
    for (var i = 0; i < all.length; i++) {
      if (all[i].key === key) return all[i]
    }
    return null
  },

  axes() {
    return Object.keys(this.conf().axes).sort()
  },

  tiers() {
    return this.conf().tiers
  },

  tierIndex(id) {
    var tiers = this.tiers()
    for (var i = 0; i < tiers.length; i++) {
      if (tiers[i].id === id) return i
    }
    return -1
  },

  // Creates the objectives that are missing, and recreates one whose criterion changed in karma.toml.
  // Also the dummy display objectives `ttl.karma` (score) and `ttl.k.<axis>` (axis scores) from CLAUDE.md.
  ensure(server) {
    var board = server.getScoreboard()
    var self = this
    this.stats().forEach(s => {
      if (!s.criterion) return
      var name = self.OBJ + s.key
      var obj = board.getObjective(name)
      if (obj && String(obj.getCriteria().getName()) === s.criterion) return
      if (obj) {
        console.warn(`[ttl] karma: ${name} changed criterion to ${s.criterion}; recreating it (resets it for players mid-Life 1)`)
        server.runCommandSilent(`scoreboard objectives remove ${name}`)
      }
      server.runCommandSilent(`scoreboard objectives add ${name} ${s.criterion}`)
      if (!board.getObjective(name)) console.error(`[ttl] karma: could not create objective ${name} (${s.criterion})`)
    })
    ;['ttl.karma'].concat(this.axes().map(a => `ttl.k.${a}`)).forEach(name => {
      if (!board.getObjective(name)) server.runCommandSilent(`scoreboard objectives add ${name} dummy`)
    })
  },

  // Current value of one stat for the player (lifetime for objectives, Life 1 for tracked ones).
  value(server, player, s) {
    if (s.track) return player.persistentData.getInt(this.TRACKED[s.track])
    try {
      var board = server.getScoreboard()
      var obj = board.getObjective(this.OBJ + s.key)
      if (!obj) return 0
      var info = board.getPlayerScoreInfo(player, obj)
      return info ? info.value() : 0
    } catch (e) {
      console.error(`[ttl] karma: reading ${this.OBJ}${s.key} for ${player.username} failed: ${e}`)
      return 0
    }
  },

  // {key: value} of every objective-backed stat, for the Life 1 start snapshot.
  snapshot(server, player) {
    var out = {}
    var self = this
    this.stats().forEach(s => {
      if (s.criterion) out[s.key] = self.value(server, player, s)
    })
    return out
  },

  base(player) {
    var raw = String(player.persistentData.getString('ttl.karma.base'))
    return raw ? JSON.parse(raw) : {}
  },

  // What the player did in Life 1 so far: {key: amount}, never negative.
  deeds(server, player) {
    var base = this.base(player)
    var out = {}
    var self = this
    this.stats().forEach(s => {
      var v = self.value(server, player, s) - (s.track ? 0 : (base[s.key] || 0))
      out[s.key] = v > 0 ? v : 0
    })
    return out
  },

  // The verdict for a set of deeds: axis raw karma and scores, total score, days, bosses, tier, dark.
  judge(deeds) {
    var conf = this.conf()
    var raw = {}
    this.axes().forEach(a => { raw[a] = 0 })
    var kinds = 0
    var bosses = 0
    this.stats().forEach(s => {
      var v = deeds[s.key] || 0
      if (s.kind) {
        if (v > 0) kinds++
        return
      }
      if (s.major && v > 0) bosses++
      if (s.axis && raw[s.axis] !== undefined) raw[s.axis] += (s.weight || 0) * v / (s.per || 1)
    })
    if (raw[conf.hostiles.axis] !== undefined) raw[conf.hostiles.axis] += conf.hostiles.weight_per_kind * kinds
    var axes = {}
    var total = 0
    var best = 0
    this.axes().forEach(a => {
      var score = 100 * Math.log(1 + raw[a] / conf.axes[a].k)
      var weighted = score * conf.axes[a].weight
      axes[a] = score
      total += weighted
      if (weighted > best) best = weighted
    })
    total += conf.best_axis_bonus * best
    var days = Math.floor((deeds.play_time || 0) / conf.ticks_per_day)
    var tier = this.tiers()[0]
    this.tiers().forEach(t => {
      if (total >= (t.min_score || 0) && days >= (t.min_days || 0) && bosses >= (t.min_bosses || 0)) tier = t
    })
    var dark = conf.dark
    var chaos = axes.chaos || 0
    var isDark = chaos >= dark.min_score && (!dark.must_beat || chaos >= (axes[dark.must_beat] || 0))
    var rounded = {}
    var rawRounded = {}
    Object.keys(axes).forEach(a => {
      rounded[a] = Math.round(axes[a])
      rawRounded[a] = Math.round(raw[a] * 10) / 10
    })
    return { score: Math.round(total), axes: rounded, raw: rawRounded, kinds: kinds, bosses: bosses, days: days, tier: tier.id, dark: isDark }
  },

  // Life 1 start (join.js for new players, /ttl reset): forget the old record, snapshot the objectives.
  startLife(server, player) {
    var data = player.persistentData
    try {
      this.ensure(server)
      String(data.getString('ttl.karma.bonus')).split(',').forEach(s => {
        if (s) server.runCommandSilent(`quietly tensura edit ability revoke ${player.username} ${s}`)
      })
      this.KEYS.concat(this.axes().map(a => `ttl.karma.${a}`)).forEach(k => data.remove(k))
      Object.keys(this.TRACKED).forEach(t => data.remove(this.TRACKED[t]))
      this.tiers().forEach(t => player.stages.remove(`ttl.tier.${t.id}`))
      player.stages.remove('ttl.tier.dark')
      data.putString('ttl.karma.base', JSON.stringify(this.snapshot(server, player)))
    } catch (e) {
      console.error(`[ttl] karma: starting Life 1 for ${player.username} failed: ${e}`)
    }
    data.putLong('ttl.l1.start', Date.now())
  },

  // Life 1 death (death.js): judge the life and keep the record for the Corridor, Life 2 and /ttl inspect.
  close(server, player) {
    var name = player.username
    var data = player.persistentData
    try {
      var deeds = this.deeds(server, player)
      var verdict = this.judge(deeds)
      var kept = {}
      Object.keys(deeds).forEach(k => { if (deeds[k] > 0) kept[k] = deeds[k] })
      verdict.deeds = kept
      verdict.at = Date.now()
      data.putString('ttl.karma.life1', JSON.stringify(verdict))
      Object.keys(verdict.raw).forEach(a => data.putInt(`ttl.karma.${a}`, Math.round(verdict.raw[a])))
      data.putInt('ttl.karma.score', verdict.score)
      data.putBoolean('ttl.karma.dark', verdict.dark)
      data.putString('ttl.tier', verdict.tier)
      data.putInt('ttl.l1.days', verdict.days)
      player.stages.add(`ttl.tier.${verdict.tier}`)
      if (verdict.dark) player.stages.add('ttl.tier.dark')
      server.runCommandSilent(`scoreboard players set ${name} ttl.karma ${verdict.score}`)
      Object.keys(verdict.axes).forEach(a => server.runCommandSilent(`scoreboard players set ${name} ttl.k.${a} ${verdict.axes[a]}`))
      console.info(`[ttl] karma: ${name} judged ${verdict.tier}${verdict.dark ? ' (dark)' : ''}, score ${verdict.score}, ${verdict.days} days, ${verdict.bosses} bosses`)
    } catch (e) {
      console.error(`[ttl] karma: judging ${name} failed, the default tier applies: ${e}`)
    }
  },

  // The stored Life 1 verdict, or null (still in Life 1, or died before karma existed).
  record(player) {
    var raw = String(player.persistentData.getString('ttl.karma.life1'))
    return raw ? JSON.parse(raw) : null
  },

  // The stored verdict, or a live preview for a player still in Life 1 (`preview: true`).
  current(server, player) {
    var rec = this.record(player)
    if (rec) return rec
    if (TtlLife.phase(player) !== 'life1') return null
    var deeds = this.deeds(server, player)
    var verdict = this.judge(deeds)
    var kept = {}
    Object.keys(deeds).forEach(k => { if (deeds[k] > 0) kept[k] = deeds[k] })
    verdict.deeds = kept
    verdict.preview = true
    return verdict
  },

  tierOf(player) {
    var rec = this.record(player)
    var i = this.tierIndex(rec ? rec.tier : this.conf().default_tier)
    return this.tiers()[i < 0 ? 0 : i]
  },

  isDark(player) {
    var rec = this.record(player)
    return !!(rec && rec.dark)
  },

  // Unique options at rebirth without the Trial (1 = random draw). corridor_flow.js asks this.
  uniqueChoices(player) {
    var n = this.tierOf(player).unique_choices || 1
    return Math.max(1, Math.min(3, n))
  },

  // Rarity weights for this soul's unique draws (TtlRegistry.draw's optional argument), or undefined.
  drawWeights(player) {
    return this.tierOf(player).weights
  },

  // Rebirth (corridor_flow.js): the tier's bonus_count non-unique skills from bonus_skills. Not uniques, so
  // straight through Tensura rather than the registry. Remembered in `ttl.karma.bonus` (/ttl reset takes them back).
  grantBonus(server, player) {
    var name = player.username
    try {
      var tier = this.tierOf(player)
      var pool = (tier.bonus_skills || []).slice()
      var given = []
      while (given.length < (tier.bonus_count || 0) && pool.length > 0) {
        var skill = pool.splice(Math.floor(Math.random() * pool.length), 1)[0]
        server.runCommandSilent(`quietly tensura edit ability grant ${name} ${skill}`)
        given.push(skill)
      }
      if (given.length === 0) return
      player.persistentData.putString('ttl.karma.bonus', given.join(','))
      TtlCorridor.voice(server, name, `Your first life was not forgotten. You also carry ${given.map(s => TtlCorridor.title(s)).join(' and ')}.`)
      console.info(`[ttl] karma: ${name} carries ${given.join(', ')} from a ${tier.id} life`)
    } catch (e) {
      console.error(`[ttl] karma: bonus skills for ${name} failed: ${e}`)
    }
  },

  // Race offers for the Corridor (TtlLife.rollOffers): Slime, then the guaranteed draws, then the rest at
  // random from the cumulative pool. Race paths without namespace, as `ttl.offers` stores them.
  offers(player) {
    var tiers = this.tiers()
    var idx = this.tierIndex(this.tierOf(player).id)
    var tier = tiers[idx]
    var dark = this.isDark(player)
    var darkRaces = this.conf().dark.races
    var offers = ['slime']
    var take = list => {
      var free = list.filter(r => offers.indexOf(r) < 0)
      if (free.length === 0) return false
      offers.push(free[Math.floor(Math.random() * free.length)])
      return true
    }
    // Draws `count` from the lists of tier idx, falling back to lower tiers once a list runs dry.
    var drawDown = (count, listOf) => {
      for (var i = idx; i >= 0 && count > 0; i--) {
        while (count > 0 && offers.length < tier.offers && take(listOf(tiers[i]) || [])) count--
      }
    }
    if (dark) drawDown(this.conf().dark.guaranteed, t => darkRaces[t.id])
    drawDown(tier.guaranteed || 0, t => t.races)
    var pool = []
    for (var i = 0; i <= idx; i++) {
      pool = pool.concat(tiers[i].races)
      if (dark) pool = pool.concat(darkRaces[tiers[i].id] || [])
    }
    while (offers.length < tier.offers && take(pool)) { /* draw until full or the pool runs dry */ }
    return offers
  },

  // Every race a dark soul of this tier could be offered on top of its normal pool (for tests and the view).
  darkPool(tierId) {
    var tiers = this.tiers()
    var idx = this.tierIndex(tierId)
    var out = []
    for (var i = 0; i <= idx; i++) out = out.concat(this.conf().dark.races[tiers[i].id] || [])
    return out
  },

  // Test/admin hook: makes the player's Life 1 amount of `key` exactly n.
  set(server, player, key, n) {
    var s = this.stat(key)
    if (!s) throw `unknown karma stat ${key}`
    if (s.track) {
      player.persistentData.putInt(this.TRACKED[s.track], n)
      return
    }
    var base = this.base(player)[key] || 0
    server.runCommandSilent(`scoreboard players set ${player.username} ${this.OBJ}${key} ${base + n}`)
  },

  // One line for /ttl inspect.
  brief(server, player) {
    var v = this.current(server, player)
    if (!v) return `tier=${this.conf().default_tier}(default)`
    var bonus = String(player.persistentData.getString('ttl.karma.bonus'))
    return `tier=${v.tier}${v.preview ? '(preview)' : ''} karma=${v.score} dark=${v.dark} days=${v.days} bosses=${v.bosses}${bonus ? ` bonus=${bonus}` : ''}`
  }
}
