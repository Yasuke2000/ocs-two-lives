// priority: 68
// Artificer commissions (design/architecture/paths-necro-artificer.md §3.5; artifice.toml [[commission]]). Guild-style
// contracts from Kaijin's forge, the Dwargon smithy and (later) Vester. A daily board, `[commissions] board` per tier, drawn
// by weight on the UTC date (server `ttl.artifice.board` = {date, tiers: {"1": [ids] ...}}). A chartered soul takes those
// of its rank's tier and below, once per day each; accepted commissions share the Free Guild's max_active with its
// bounties. The hand-in takes the items from the inventory; `made_by = true` counts only stacks carrying the soul's own
// maker's stamp (artifice.js). Rewards: coins (TtlEcon.pay), reputation (TtlRep.add), artifice points (tier or `points`),
// and sometimes a gated schematic (O-A2). Player record: ttl.artifice `jobs` {"<date>:<id>": {id, at}} and `done`
// (the last 40 keys).
//
// PUBLIC API
//   TtlCommission.find(id) · board(server) [{n, c}] · check(server, player, id) '' or the reason it cannot be taken
//   TtlCommission.take(server, player, ref) · turnin(server, player) n handed in · abandon(server, player, ref)
//   TtlCommission.force(server, player, id)      test hook: accept a commission that is not on today's board
//   TtlCommission.ready(server, player, c) · have(server, player, item, madeBy) how many count
//   TtlCommission.handIn(server, player, {item, count, made_by})  RESERVED for the radiant boards (WP-W13/A3, kind
//                         `collect` with made_by): true when the items were there and are now taken, else false
const TtlCommission = {
  BOARD: 'ttl.artifice.board',

  conf() {
    return TtlArtifice.conf()
  },

  all() {
    return this.conf().commission || []
  },

  find(id) {
    var list = this.all()
    for (var i = 0; i < list.length; i++) {
      if (String(list[i].id) === String(id)) return list[i]
    }
    return null
  },

  // ---- the board ---------------------------------------------------------------------------------------------------

  roll(server, force) {
    var date = TtlArtifice.dateKey()
    var b = {}
    try {
      b = JSON.parse(String(server.persistentData.getString(this.BOARD)) || '{}')
    } catch (e) {
      b = {}
    }
    if (!force && b.date === date && b.tiers) return b
    var per = Number((this.conf().commissions || {}).board || 2)
    var tiers = {}
    var self = this
    ;[1, 2, 3, 4].forEach(t => {
      var pool = self.all().filter(c => Number(c.tier) === t)
      var picked = []
      while (picked.length < per && pool.length > 0) {
        var total = pool.reduce((sum, c) => sum + Number(c.weight), 0)
        var r = Math.random() * total
        var at = 0
        for (var i = 0; i < pool.length; i++) {
          r -= Number(pool[i].weight)
          if (r < 0) {
            at = i
            break
          }
        }
        picked.push(String(pool[at].id))
        pool.splice(at, 1)
      }
      tiers[String(t)] = picked
    })
    b = { date: date, tiers: tiers }
    server.persistentData.putString(this.BOARD, JSON.stringify(b))
    console.info(`[ttl] artifice: commission board ${date}: ${JSON.stringify(tiers)}`)
    return b
  },

  // Numbered entries [{n, c}] of today's board, tier 1 first.
  board(server) {
    var b = this.roll(server, false)
    var out = []
    var self = this
    ;['1', '2', '3', '4'].forEach(t => (b.tiers[t] || []).forEach(id => {
      var c = self.find(id)
      if (c) out.push({ n: out.length + 1, c: c })
    }))
    return out
  },

  ref(server, ref) {
    var list = this.board(server)
    var n = Number(ref)
    for (var i = 0; i < list.length; i++) {
      if ((n > 0 && list[i].n === n) || String(list[i].c.id) === String(ref)) return list[i].c
    }
    return null
  },

  // ---- the player's side --------------------------------------------------------------------------------------------

  key(c) {
    return `${TtlArtifice.dateKey()}:${c.id}`
  },

  prune(s) {
    var today = TtlArtifice.dateKey()
    Object.keys(s.jobs).forEach(k => {
      // A commission accepted on an earlier day stays accepted until it is handed in or abandoned.
      if (!s.jobs[k] || !s.jobs[k].id) delete s.jobs[k]
    })
    s.done = s.done.filter(k => k.indexOf(today) === 0).slice(-40)
  },

  guildTaken(player) {
    try {
      if (typeof TtlGuild !== 'undefined') return Object.keys(TtlGuild.read(player).taken || {}).length
    } catch (e) {
      console.warn(`[ttl] artifice: guild record of ${player.username} unreadable: ${e}`)
    }
    return 0
  },

  maxActive() {
    try {
      return Number(TtlData.economy.guild.max_active)
    } catch (e) {
      return 3
    }
  },

  jobFor(s, id) {
    var keys = Object.keys(s.jobs)
    for (var i = 0; i < keys.length; i++) {
      if (String(s.jobs[keys[i]].id) === String(id)) return keys[i]
    }
    return ''
  },

  check(server, player, id) {
    if (TtlLife.phase(player) !== 'life2') return 'life2only'
    var c = this.find(id)
    if (!c) return `no commission ${id}`
    var s = TtlArtifice.read(player)
    if (s.rank < 1) return 'needs the artificer charter (/ttl artifice charter at a Workshop Bench)'
    var def = TtlArtifice.rankDef(s.rank)
    if (Number(c.tier) > Number(def.tier)) return `needs rank ${c.tier} (${TtlArtifice.rankDef(c.tier).title})`
    this.prune(s)
    if (this.jobFor(s, c.id)) return 'already accepted'
    if (s.done.indexOf(this.key(c)) >= 0) return 'already done today'
    var open = Object.keys(s.jobs).length + this.guildTaken(player)
    if (open >= this.maxActive()) return `you already carry ${this.maxActive()} contracts (guild bounties count too)`
    return ''
  },

  accept(server, player, c) {
    var s = TtlArtifice.read(player)
    this.prune(s)
    s.jobs[this.key(c)] = { id: String(c.id), at: Date.now() }
    TtlArtifice.write(player, s)
    console.info(`[ttl] artifice: ${player.username} took the commission ${c.id}`)
    player.tell(Text.gold(`Workshop: you took "${c.title}": ${c.count} x ${this.pretty(c.item)}${c.made_by ? ', made by your own hand' : ''}.`))
    return c
  },

  take(server, player, ref) {
    var c = this.ref(server, ref)
    if (!c) throw `no such commission on today's board: ${ref}`
    var why = this.check(server, player, c.id)
    if (why) throw why
    return this.accept(server, player, c)
  },

  force(server, player, id) {
    var c = this.find(id)
    if (!c) throw `no commission ${id}`
    var why = this.check(server, player, id)
    if (why) throw why
    return this.accept(server, player, c)
  },

  abandon(server, player, ref) {
    var s = TtlArtifice.read(player)
    var c = this.find(ref) || this.ref(server, ref)
    var key = c ? this.jobFor(s, c.id) : ''
    if (!key) throw `you have not accepted ${ref}`
    delete s.jobs[key]
    TtlArtifice.write(player, s)
    return c
  },

  counts(server, player, stack, item, madeBy) {
    if (stack.isEmpty() || String(stack.id) !== String(item)) return false
    return !madeBy || TtlArtifice.isMine(server, player, stack)
  },

  have(server, player, item, madeBy) {
    var n = 0
    var inv = player.getInventory()
    for (var i = 0; i < inv.getContainerSize(); i++) {
      var st = inv.getItem(i)
      if (this.counts(server, player, st, item, madeBy)) n += Number(st.count)
    }
    return n
  },

  ready(server, player, c) {
    return this.have(server, player, c.item, !!c.made_by) >= Number(c.count)
  },

  takeItems(server, player, item, count, madeBy) {
    var left = Number(count)
    var inv = player.getInventory()
    for (var i = 0; i < inv.getContainerSize() && left > 0; i++) {
      var st = inv.getItem(i)
      if (!this.counts(server, player, st, item, madeBy)) continue
      var k = Math.min(left, Number(st.count))
      st.shrink(k)
      left -= k
    }
    inv.setChanged()
    return left === 0
  },

  handIn(server, player, spec) {
    var count = Number(spec.count || 1)
    if (this.have(server, player, spec.item, !!spec.made_by) < count) return false
    return this.takeItems(server, player, spec.item, count, !!spec.made_by)
  },

  pay(server, player, c) {
    var rw = c.reward || {}
    var coins = 0
    try {
      coins = TtlEcon.pay(server, player, rw.coins || 0, `commission:${c.id}`)
    } catch (e) {
      console.error(`[ttl] artifice: paying ${c.id} to ${player.username} failed: ${e}`)
    }
    var rep = rw.rep || {}
    Object.keys(rep).forEach(f => {
      try {
        if (typeof TtlRep !== 'undefined') TtlRep.add(server, player, f, Number(rep[f]), `commission ${c.id}`)
      } catch (e) {
        console.error(`[ttl] artifice: reputation for ${c.id} (${f}) failed: ${e}`)
      }
    })
    if (rw.schematic) {
      server.runCommandSilent(`give ${player.username} ${rw.schematic}`)
      player.tell(Text.gold(`Workshop: the client adds a schematic to your pay: ${this.pretty(rw.schematic)}.`))
    }
    var tierPts = ((TtlArtifice.conf().points || {}).commission || [])[Number(c.tier) - 1]
    var pts = TtlArtifice.addPoints(server, player, 'commission', rw.points !== undefined ? Number(rw.points) : Number(tierPts || 0), `commission ${c.id}`)
    return { coins: coins, points: pts }
  },

  turnin(server, player) {
    if (TtlLife.phase(player) !== 'life2') throw 'life2only'
    var s = TtlArtifice.read(player)
    this.prune(s)
    var keys = Object.keys(s.jobs)
    if (keys.length === 0) throw 'you have no accepted commissions (/ttl artifice commissions)'
    var count = 0
    var self = this
    keys.forEach(k => {
      var c = self.find(s.jobs[k].id)
      if (!c) {
        delete s.jobs[k]
        return
      }
      if (!self.ready(server, player, c)) return
      if (!self.takeItems(server, player, c.item, c.count, !!c.made_by)) return
      delete s.jobs[k]
      s.done.push(self.key(c))
      TtlArtifice.write(player, s)
      var paid = self.pay(server, player, c)
      s = TtlArtifice.read(player)
      self.prune(s)
      s.last = { id: String(c.id), coins: paid.coins, points: paid.points }
      TtlArtifice.write(player, s)
      count++
      console.info(`[ttl] artifice: ${player.username} delivered ${c.id}: ${paid.coins} bronze, +${paid.points} points`)
      player.tell(Text.green(`Workshop: "${c.title}" delivered. Paid ${TtlEcon.text(paid.coins)}.`))
      self.announce(server, player, c)
      TtlArtifice.emit(server, player, 'commission', { id: String(c.id), tier: Number(c.tier) })
    })
    if (count === 0) {
      TtlArtifice.write(player, s)
      throw 'nothing is ready yet: bring the items (made by your own hand where the commission says so)'
    }
    return count
  },

  announce(server, player, c) {
    var at = Number((this.conf().commissions || {}).announce_tier || 99)
    if (Number(c.tier) < at || TtlArtifice.isBot(player)) return
    try {
      if (typeof TtlDiscord !== 'undefined') TtlDiscord.post(server, `${TtlDiscord.name(String(player.username))} delivered a masterwork commission: *${c.title}*.`)
    } catch (e) {
      console.warn(`[ttl] artifice: commission announcement failed: ${e}`)
    }
  },

  // ---- display --------------------------------------------------------------------------------------------------------

  pretty(id) {
    var path = String(id).split(':').pop()
    return path.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  },

  rewardText(c) {
    var rw = c.reward || {}
    var parts = []
    try {
      if (rw.coins) parts.push(TtlEcon.text(rw.coins))
    } catch (e) {
      // coins unreadable: leave them out of the text
    }
    Object.keys(rw.rep || {}).forEach(f => parts.push(`${f} +${rw.rep[f]}`))
    if (rw.schematic) parts.push(`a ${this.pretty(rw.schematic)}`)
    return parts.join(', ')
  },

  lines(server, player) {
    var s = TtlArtifice.read(player)
    this.prune(s)
    var def = TtlArtifice.rankDef(s.rank)
    var out = [`Commissions on the workshop board today (${def ? `you may take tier ${def.tier} and below` : 'take the charter first'}):`]
    var self = this
    var board = this.board(server)
    board.forEach(e => {
      var c = e.c
      var state = self.jobFor(s, c.id) ? (self.ready(server, player, c) ? 'ready to deliver' : `accepted ${self.have(server, player, c.item, !!c.made_by)}/${c.count}`)
        : s.done.indexOf(self.key(c)) >= 0 ? 'done today' : ''
      out.push(`${e.n}. [T${c.tier}] ${c.title}: ${c.count} x ${self.pretty(c.item)}${c.made_by ? ' (your own work)' : ''} -> ${self.rewardText(c)}${state ? ` [${state}]` : ''}`)
    })
    var mine = Object.keys(s.jobs).map(k => s.jobs[k].id).filter(id => !board.some(e => String(e.c.id) === String(id)))
    if (mine.length) out.push(`Also accepted (earlier boards): ${mine.join(', ')}`)
    return out
  }
}
