// priority: 71
// World's Favor (design/architecture/sprint3-4.md S6; knobs: design/data/events.toml [favor]). The weekly `favor` event
// of the director calls TtlFavor.run: it picks one struggling but active Life 2 player and offers 3 blessings; the
// player chooses one with /ttl favor choose <id> (or the menu). Blessings tie to the rest of the pack: the Common unique
// goes through TtlRegistry (golden rule 1), EP through Tensura's own edit command.
//
// Eligible: online, Life 2, played >= min_hours this week (ttl.play.week, ticks, counted only in Life 2 and kept up
// to date by track() on the director's one-minute loop), no Favor offered within cooldown_days, no open offer, a
// linked Discord account when require_discord (skipped without the sdlink bridge and for test bots). The winner comes
// from the lowest bottom_pct percent by EP.
//
// Player persistentData: ttl.play.week/wk/last (weekly play ticks, week id, last sample), ttl.favor.offer ("a,b,c"),
// ttl.favor.until (epoch ms). Server persistentData: ttl.favor.last {uuid: epoch ms of the last offer},
// ttl.favor.winner (name of the latest pick, for tests and /ttl events).
const TtlFavor = {
  TICKS_PER_HOUR: 72000,
  WEEK: 604800000,

  conf() {
    var f = (typeof TtlData !== 'undefined' && TtlData.events && TtlData.events.favor) || {}
    var n = (v, d) => TtlEvents.num(v, d)
    return {
      bottom_pct: n(f.bottom_pct, 25),
      min_hours: n(f.min_hours, 5),
      cooldown_days: n(f.cooldown_days, 30),
      require_discord: f.require_discord !== false,
      offer_hours: n(f.offer_hours, 48),
      offer_count: n(f.offer_count, 3),
      choices: f.choices || [],
      choice: f.choice || {}
    }
  },

  // ---- weekly play time (Life 2 only) ---------------------------------------------------------------------------

  // Monday-based week number in Brussels time.
  weekId(now) {
    var l = TtlEvents.local(now)
    var day = Math.floor(Date.UTC(l.y, l.m, l.d) / TtlEvents.DAY)
    return Math.floor((day + 3) / 7)
  },

  playTicks(server, player) {
    try {
      var board = server.getScoreboard()
      var obj = board.getObjective('ttl.play')
      if (!obj) return null
      var info = board.getPlayerScoreInfo(player, obj)
      return info ? Number(info.value()) : 0
    } catch (e) {
      console.warn(`[ttl] favor: reading play time of ${player.username} failed: ${e}`)
      return null
    }
  },

  // One pass per director loop: adds the ticks played since the last sample to the player's week while they are in Life 2.
  track(server) {
    var wk = this.weekId(Date.now())
    var self = this
    server.getPlayerList().getPlayers().forEach(p => {
      var cur = self.playTicks(server, p)
      if (cur === null) return
      var d = p.persistentData
      var last = d.contains('ttl.play.last') ? d.getInt('ttl.play.last') : cur
      if (d.getInt('ttl.play.wk') !== wk) {
        d.putInt('ttl.play.wk', wk)
        d.putInt('ttl.play.week', 0)
      }
      var delta = cur - last
      if (delta > 0 && TtlLife.phase(p) === 'life2') d.putInt('ttl.play.week', d.getInt('ttl.play.week') + delta)
      d.putInt('ttl.play.last', cur)
    })
  },

  weekHours(player) {
    var d = player.persistentData
    if (d.getInt('ttl.play.wk') !== this.weekId(Date.now())) return 0
    return d.getInt('ttl.play.week') / this.TICKS_PER_HOUR
  },

  // Test hook (/ttl events setup): this week's play time in whole hours.
  setWeekHours(player, hours) {
    var d = player.persistentData
    d.putInt('ttl.play.wk', this.weekId(Date.now()))
    d.putInt('ttl.play.week', Math.round(Number(hours) * this.TICKS_PER_HOUR))
  },

  // ---- eligibility ------------------------------------------------------------------------------------------------

  ep(player) {
    try {
      return Number(Java.loadClass('io.github.manasmods.tensura.storage.TensuraStorages').getExistenceFrom(player).getEP())
    } catch (e) {
      console.warn(`[ttl] favor: reading the EP of ${player.username} failed: ${e}`)
      return null
    }
  },

  last(server) {
    return TtlEvents.read(server, 'ttl.favor.last', {})
  },

  onCooldown(server, player) {
    var at = this.last(server)[TtlLife.uuid(player)]
    return !!at && Date.now() - at < this.conf().cooldown_days * TtlEvents.DAY
  },

  hasOffer(player) {
    var d = player.persistentData
    if (!String(d.getString('ttl.favor.offer'))) return false
    return Number(String(d.getString('ttl.favor.until')) || 0) > Date.now()
  },

  discordLinked(player) {
    if (typeof TtlDiscord !== 'undefined' && TtlDiscord.isBot(player.username)) return true
    if (typeof TtlSdlink === 'undefined' || !TtlSdlink.load()) return true
    return !!TtlSdlink.discordId(TtlLife.uuid(player))
  },

  // Why this player is not eligible, or null.
  reason(server, player, c) {
    if (TtlLife.phase(player) !== 'life2') return 'not in Life 2'
    if (this.weekHours(player) < c.min_hours) return `played ${this.weekHours(player).toFixed(1)} h this week (< ${c.min_hours})`
    if (this.onCooldown(server, player)) return 'Favor cooldown'
    if (this.hasOffer(player)) return 'has an open offer'
    if (c.require_discord && !this.discordLinked(player)) return 'no linked Discord account'
    return null
  },

  // [{player, ep}] of the eligible players, lowest EP first.
  eligible(server) {
    var c = this.conf()
    var out = []
    var self = this
    server.getPlayerList().getPlayers().forEach(p => {
      var why = self.reason(server, p, c)
      if (why) return
      var ep = self.ep(p)
      if (ep === null) return
      out.push({ player: p, ep: ep })
    })
    out.sort((a, b) => a.ep - b.ep)
    return out
  },

  // The winner among the bottom bottom_pct percent by EP, or null.
  pick(server) {
    var list = this.eligible(server)
    if (list.length === 0) return null
    var k = Math.max(1, Math.ceil(list.length * this.conf().bottom_pct / 100))
    return list[Math.floor(Math.random() * k)].player
  },

  // ---- blessings -----------------------------------------------------------------------------------------------------

  commonPool() {
    return (typeof TtlData !== 'undefined' && TtlData.skills && TtlData.skills.common && TtlData.skills.common.skills) || []
  },

  // Blessing ids that can be given to this player right now (a Common unique needs one that is free).
  usable(server, player, c) {
    var self = this
    return c.choices.filter(id => {
      if (!c.choice[id]) return false
      if (id === 'common_unique') return TtlRegistry.draw(server, self.commonPool(), 1, player.username).length > 0
      return true
    })
  },

  rollOffer(server, player) {
    var c = this.conf()
    var pool = this.usable(server, player, c)
    var out = []
    while (out.length < c.offer_count && pool.length > 0) out.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0])
    return out
  },

  // Gives the player an offer of these blessings and shows the menu.
  offer(server, player, ids) {
    var c = this.conf()
    var d = player.persistentData
    d.putString('ttl.favor.offer', ids.join(','))
    d.putString('ttl.favor.until', String(Date.now() + c.offer_hours * TtlEvents.HOUR))
    var last = this.last(server)
    last[TtlLife.uuid(player)] = Date.now()
    TtlEvents.write(server, 'ttl.favor.last', last)
    server.persistentData.putString('ttl.favor.winner', String(player.username))
    console.info(`[ttl] favor: ${player.username} is offered ${ids.join(', ')}`)
    this.show(server, player)
  },

  show(server, player) {
    var d = player.persistentData
    var ids = String(d.getString('ttl.favor.offer')).split(',').filter(s => s)
    if (ids.length === 0 || !this.hasOffer(player)) return false
    var c = this.conf()
    var name = String(player.username)
    var slots = ids.length === 1 ? [13] : ids.length === 2 ? [12, 14] : [11, 13, 15]
    var items = ids.map((id, i) => {
      var b = c.choice[id] || {}
      return {
        slot: slots[i], item: b.icon || 'minecraft:paper', name: b.label || id, color: '#FFD966',
        lore: TtlCorridor.wrap(b.lore || '', 34), command: `ttl favor choose ${id}`
      }
    })
    try {
      TtlCorridor.menu(server, player, "World's Favor: choose a blessing", 3, items, null)
      TtlCorridor.buttons(server, name, "The world's gaze rests on you. Choose a blessing.", [{ label: 'Open', command: '/ttl favor', hover: 'Reopen the choices' }])
    } catch (e) {
      console.warn(`[ttl] favor: menu for ${name} failed, chat fallback: ${e}`)
      server.runCommandSilent(`tellraw ${name} ${JSON.stringify([{ text: "[World's Favor] Choose with /ttl favor choose <id>: " + ids.join(', '), color: 'gold' }])}`)
    }
    return true
  },

  // Applies one blessing; returns an error string (nothing consumed) or null.
  apply(server, player, id) {
    var c = this.conf()
    var b = c.choice[id]
    var name = String(player.username)
    if (!b) return `unknown blessing ${id}`
    if (id === 'common_unique') {
      var drawn = TtlRegistry.draw(server, this.commonPool(), 1, name)
      if (drawn.length === 0) return 'No Common unique is free right now. Choose another blessing.'
      if (!TtlRegistry.grant(server, player, drawn[0], "World's Favor")) return 'The world could not grant that skill. Choose another blessing.'
      console.info(`[ttl] favor: ${name} received ${drawn[0]}`)
      return null
    }
    if (id === 'ep_surge') {
      var ep = this.ep(player)
      var gain = Math.max(TtlEvents.num(b.gain_min, 0), Math.round((ep || 0) * TtlEvents.num(b.gain_pct, 0) / 100))
      server.runCommandSilent(`quietly tensura edit stat ${name} ep current add ${gain}`)
      console.info(`[ttl] favor: ${name} gained ${gain} EP`)
      return null
    }
    if (id === 'resistance') {
      var skills = b.skills || []
      if (skills.length === 0) return 'No resistance is configured.'
      var skill = skills[Math.floor(Math.random() * skills.length)]
      server.runCommandSilent(`quietly tensura edit ability grant ${name} ${skill}`)
      console.info(`[ttl] favor: ${name} received ${skill}`)
      return null
    }
    if (id === 'protection') {
      ;(b.effects || []).forEach(e => server.runCommandSilent(`effect give ${name} ${e.id} ${e.seconds} ${e.amplifier || 0} true`))
      console.info(`[ttl] favor: ${name} protected`)
      return null
    }
    if (id === 'relic') {
      ;(b.items || []).forEach(i => server.runCommandSilent(`give ${name} ${i.id} ${i.count || 1}`))
      console.info(`[ttl] favor: ${name} received a relic`)
      return null
    }
    return `blessing ${id} has no effect`
  },

  // /ttl favor choose <id> as the winner. Returns an error string or null.
  choose(server, player, id) {
    var d = player.persistentData
    if (!this.hasOffer(player)) return 'You have no open blessing.'
    var ids = String(d.getString('ttl.favor.offer')).split(',')
    if (ids.indexOf(id) < 0) return `That blessing is not on offer. Choose one of: ${ids.join(', ')}.`
    var error = this.apply(server, player, id)
    if (error) return error
    d.remove('ttl.favor.offer')
    d.remove('ttl.favor.until')
    server.runCommandSilent(`tellraw ${player.username} ${JSON.stringify([{ text: "[World's Favor] ", color: 'gold' }, { text: `The world grants you: ${(this.conf().choice[id] || {}).label || id}.`, color: 'yellow' }])}`)
    return null
  },

  // Called by the director for the `favor` action. false = nobody eligible now (the director retries).
  run(server, ctx) {
    var winner = this.pick(server)
    if (!winner) {
      console.info(`[ttl] favor: nobody eligible online (${this.eligible(server).length} eligible)`)
      return false
    }
    var ids = this.rollOffer(server, winner)
    if (ids.length === 0) return false
    this.offer(server, winner, ids)
    return { player: String(winner.username) }
  },

  // Test and ops hook: clears offer, cooldown and week of a player.
  clear(server, player) {
    var d = player.persistentData
    ;['ttl.favor.offer', 'ttl.favor.until', 'ttl.play.week', 'ttl.play.wk', 'ttl.play.last'].forEach(k => d.remove(k))
    var last = this.last(server)
    delete last[TtlLife.uuid(player)]
    TtlEvents.write(server, 'ttl.favor.last', last)
  }
}
