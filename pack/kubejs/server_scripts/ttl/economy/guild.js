// priority: 70
// Fuze's Free Guild: the Adventurer's Guild bounty board (design/architecture/sprint3-4.md S7; numbers in
// design/data/economy.toml -> TtlData.economy). Life 2 only. The main coin faucet (economy/sinks.js pays it out).
//
//   Board    3 daily + 2 weekly bounties, drawn by weight from the TOML pool, rolled on the UTC date (daily) and the ISO
//            week starting Monday (weekly). One daily slot is always a bounty for the lowest rank. Server persistentData
//            `ttl.guild.board` = {date, week, daily: [ids], weekly: [ids]}. Slots are numbered 1.. (daily first).
//   Player   persistentData `ttl.guild` = {points, done, taken: {key: {id, period, stamp, got, last, told}}, hist: [keys]}
//            with key = "<period>:<stamp>:<id>" (a bounty can be done once per period) and `got` the progress for kill
//            and visit bounties. Rank F-S from lifetime points. Mirrors: scoreboard `ttl.bounty` (bounties done) and one
//            stage `ttl.guild.<rank letter, lower case>` for Easy NPC / FTB Quests conditions.
//   Kills    scoreboard objectives `ttl.g.<ns>_<path>` with criterion `minecraft.killed:<ns>.<path>`, sampled every
//            guild.poll_ticks (EntityEvents.death is unreliable for mobs here): the growth since the last sample counts
//            (only while the player is in the bounty's `region`, when it has one). Visits count within guild.visit_radius
//            blocks of the landmark (its placed position from `ttl.landmark.<name>.at`, else the planned x/z).
//            Deliveries are checked and taken from the inventory at hand-in.
//   Rewards  coins (TtlEcon.pay) + reputation (TtlRep.add, only when the reputation package is loaded) + guild points.
//
// Givers (guild_npcs.js places the Easy NPCs): every bounty has a `giver` (default "desk"). Fuze, the guild master,
// gives the contracts of rank guild.fuze_min_rank and up (giver "fuze"); the guild receptionists ("desk") give the rest.
// The board keeps one slot list per giver, desk first: desk slots 1-5 are what they always were, Fuze's come after
// (6, 7). Without a giver the commands behave as before (global slot numbers, everything); with a giver, numbers
// count inside that giver's list and a bounty of the other giver is refused ("wrong_giver").
//
// Entry points (commands in economy/commands.js; an Easy NPC dialog action runs the same ones as the player):
//   /ttl guild board [giver] | take <slot|id> [giver] | turnin [giver] | abandon <slot|id> | status
// Interim desks (a block, besides the NPCs): a block registered with /ttl guild desk add x y z shows the board
// when right-clicked.
const TtlGuild = {
  KEY: 'ttl.guild',
  BOARD: 'ttl.guild.board',
  GIVERS: ['desk', 'fuze'],
  DESKS: 'ttl.guild.desks',
  OBJ: 'ttl.g.',
  BOUNTY: 'ttl.bounty',

  conf() {
    return TtlData.economy
  },

  ranks() {
    return this.conf().rank
  },

  bounties() {
    return this.conf().bounty
  },

  find(id) {
    var all = this.bounties()
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  rankIndexOf(id) {
    var all = this.ranks()
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return i
    }
    return 0
  },

  rankIndexForPoints(points) {
    var all = this.ranks()
    var out = 0
    for (var i = 0; i < all.length; i++) {
      if (points >= all[i].points) out = i
    }
    return out
  },

  giverOf(b) {
    return String(b.giver || 'desk')
  },

  // 'desk' | 'fuze' | null (no filter); anything else is a typo and must not silently mean "everything".
  requireGiver(giver) {
    if (giver === null || giver === undefined || giver === '') return null
    var g = String(giver)
    if (this.GIVERS.indexOf(g) < 0) throw `unknown giver ${g} (${this.GIVERS.join(' or ')})`
    return g
  },

  // How many daily / weekly slots a giver gets (economy.toml [guild]: daily/weekly for the desk, fuze_* for Fuze).
  slotsOf(giver, period) {
    var g = this.conf().guild
    if (giver === 'fuze') return Number(period === 'daily' ? g.fuze_daily || 0 : g.fuze_weekly || 0)
    return Number(g[period])
  },

  requireLife2(player) {
    if (TtlLife.phase(player) !== 'life2') throw 'Life 2 only'
  },

  // ---- names and text ----

  pretty(id) {
    var path = String(id).replace(/^[^:]*:/, '')
    return path.split('_').map(w => (w ? w.charAt(0).toUpperCase() + w.slice(1) : w)).join(' ')
  },

  what(b) {
    if (b.kind === 'kill') return `Kill ${b.count} ${this.pretty(b.target)}`
    if (b.kind === 'deliver') return `Deliver ${b.count} ${this.pretty(b.target)}`
    return `Visit the ${this.pretty(b.target)}`
  },

  rewardText(b) {
    var rep = Object.keys(b.reward.rep || {}).map(f => `+${b.reward.rep[f]} ${f}`)
    return [TtlEcon.text(b.reward.coins)].concat(rep).concat([`${b.points} pt`]).join(', ')
  },

  // ---- objectives for kill bounties ----

  objective(target) {
    return this.OBJ + String(target).replace(/[^a-z0-9_.+-]/g, '_')
  },

  criterion(target) {
    return 'minecraft.killed:' + String(target).replace(':', '.')
  },

  // Creates the kill objectives that are missing (or recreates one whose criterion differs).
  ensureObjectives(server) {
    var board = server.getScoreboard()
    var self = this
    var seen = {}
    this.bounties().forEach(b => {
      if (b.kind !== 'kill' || seen[b.target]) return
      seen[b.target] = true
      var name = self.objective(b.target)
      var crit = self.criterion(b.target)
      var obj = board.getObjective(name)
      if (obj && String(obj.getCriteria().getName()) === crit) return
      if (obj) server.runCommandSilent(`scoreboard objectives remove ${name}`)
      server.runCommandSilent(`scoreboard objectives add ${name} ${crit}`)
      if (!board.getObjective(name)) console.error(`[ttl] guild: could not create objective ${name} (${crit})`)
    })
    if (!board.getObjective(this.BOUNTY)) server.runCommandSilent(`scoreboard objectives add ${this.BOUNTY} dummy`)
  },

  killValue(server, player, target) {
    try {
      var board = server.getScoreboard()
      var obj = board.getObjective(this.objective(target))
      if (!obj) return 0
      var info = board.getPlayerScoreInfo(player, obj)
      return info ? info.value() : 0
    } catch (e) {
      console.error(`[ttl] guild: reading ${this.objective(target)} for ${player.username} failed: ${e}`)
      return 0
    }
  },

  // ---- the board ----

  board(server) {
    var raw = String(server.persistentData.getString(this.BOARD) || '')
    var b = raw ? JSON.parse(raw) : {}
    return {
      date: b.date || '', week: b.week || '', daily: b.daily || [], weekly: b.weekly || [],
      // Missing in a board saved before the givers existed: ensure() rolls them once.
      fuzeDaily: b.fuzeDaily || [], fuzeWeekly: b.fuzeWeekly || [], givers: b.givers || 1
    }
  },

  saveBoard(server, b) {
    server.persistentData.putString(this.BOARD, JSON.stringify(b))
  },

  draw(period, n, giver) {
    var who = giver || 'desk'
    var self = this
    var pool = this.bounties().filter(b => b.period === period && b.weight > 0 && self.giverOf(b) === who)
    var picked = []
    var first = String(this.ranks()[0].id)
    var take = list => {
      var total = 0
      list.forEach(b => { total += b.weight })
      var roll = Math.random() * total
      for (var i = 0; i < list.length; i++) {
        roll -= list[i].weight
        if (roll < 0) return list[i]
      }
      return list[list.length - 1]
    }
    if (who === 'desk' && period === 'daily' && n > 0) {
      var easy = pool.filter(b => b.min_rank === first)
      if (easy.length > 0) {
        var one = take(easy)
        picked.push(one.id)
        pool = pool.filter(b => b.id !== one.id)
      }
    }
    while (picked.length < n && pool.length > 0) {
      var b = take(pool)
      picked.push(b.id)
      pool = pool.filter(x => x.id !== b.id)
    }
    return picked.map(id => String(id))
  },

  // Rolls what is stale (new UTC date / new ISO week); `force` is 'daily', 'weekly' or 'all' to roll anyway.
  ensure(server, force) {
    var b = this.board(server)
    var today = TtlEcon.dayKey()
    var week = TtlEcon.weekKey()
    var g = this.conf().guild
    var changed = false
    // A board saved before the givers existed has no Fuze lists: roll them now, the desk's lists stay.
    var firstGivers = b.givers < 2
    if (force === 'daily' || force === 'all' || b.date !== today || firstGivers) {
      if (force === 'daily' || force === 'all' || b.date !== today) b.daily = this.draw('daily', g.daily, 'desk')
      b.fuzeDaily = this.draw('daily', this.slotsOf('fuze', 'daily'), 'fuze')
      b.date = today
      changed = true
    }
    if (force === 'weekly' || force === 'all' || b.week !== week || firstGivers) {
      if (force === 'weekly' || force === 'all' || b.week !== week) b.weekly = this.draw('weekly', g.weekly, 'desk')
      b.fuzeWeekly = this.draw('weekly', this.slotsOf('fuze', 'weekly'), 'fuze')
      b.week = week
      changed = true
    }
    if (changed) {
      b.givers = 2
      this.saveBoard(server, b)
      console.info(`[ttl] guild board ${b.date} (week ${b.week}): daily ${b.daily.join(', ')}; weekly ${b.weekly.join(', ')}; ` +
        `Fuze daily ${b.fuzeDaily.join(', ') || '-'}; Fuze weekly ${b.fuzeWeekly.join(', ') || '-'}`)
    }
    return b
  },

  // Test/staff hook: puts bounty `id` into the first slot of its period.
  post(server, id) {
    var bounty = this.find(id)
    if (!bounty) throw `unknown bounty ${id}`
    var b = this.ensure(server)
    var giver = this.giverOf(bounty)
    var daily = bounty.period === 'daily'
    var list = giver === 'fuze' ? (daily ? b.fuzeDaily : b.fuzeWeekly) : (daily ? b.daily : b.weekly)
    var at = list.indexOf(bounty.id)
    if (at >= 0) list.splice(at, 1)
    list.unshift(String(bounty.id))
    list.splice(this.slotsOf(giver, bounty.period))
    this.saveBoard(server, b)
    return this.entries(server)
  },

  // [{slot, local, giver, period, stamp, b}] in slot order: the desk's daily and weekly bounties, then Fuze's. `slot` is
  // global; `local` counts inside the giver's list. With `giver` only that giver's entries (their `slot` still global).
  entries(server, giver) {
    var board = this.board(server)
    var out = []
    var count = { desk: 0, fuze: 0 }
    var self = this
    var add = (ids, period, stamp, who) => ids.forEach(id => {
      var b = self.find(id)
      if (!b) return
      count[who]++
      out.push({ slot: out.length + 1, local: count[who], giver: who, period: period, stamp: stamp, b: b })
    })
    add(board.daily, 'daily', board.date, 'desk')
    add(board.weekly, 'weekly', board.week, 'desk')
    add(board.fuzeDaily, 'daily', board.date, 'fuze')
    add(board.fuzeWeekly, 'weekly', board.week, 'fuze')
    var only = this.requireGiver(giver)
    return only ? out.filter(e => e.giver === only) : out
  },

  // `ref` is a slot number (global without a giver, the giver's own count with one) or a bounty id. With a giver a
  // bounty of the other giver is "wrong_giver", not "no such bounty": the NPC the player talks to is the one who
  // must hold it.
  entry(server, ref, giver) {
    var only = this.requireGiver(giver)
    var list = this.entries(server)
    var text = String(ref)
    for (var i = 0; i < list.length; i++) {
      var e = list[i]
      var num = only ? String(e.local) : String(e.slot)
      if (String(e.b.id) === text) {
        if (only && e.giver !== only) throw 'wrong_giver'
        return e
      }
      if (num === text && (!only || e.giver === only)) return e
    }
    return null
  },

  keyOf(e) {
    return `${e.period}:${e.stamp}:${e.b.id}`
  },

  // ---- player records ----

  read(player) {
    var raw = String(player.persistentData.getString(this.KEY) || '')
    var g = raw ? JSON.parse(raw) : {}
    g.points = g.points || 0
    g.done = g.done || 0
    g.taken = g.taken || {}
    g.hist = g.hist || []
    return g
  },

  write(player, g) {
    g.hist = g.hist.slice(-80)
    player.persistentData.putString(this.KEY, JSON.stringify(g))
  },

  // Accepted bounties of a period that has rolled over are gone.
  prune(server, g) {
    var board = this.board(server)
    var drop = []
    Object.keys(g.taken).forEach(key => {
      var t = g.taken[key]
      var stamp = t.period === 'daily' ? board.date : board.week
      if (t.stamp !== stamp) drop.push(key)
    })
    drop.forEach(key => delete g.taken[key])
    return drop.length
  },

  rankOf(g) {
    return this.ranks()[this.rankIndexForPoints(g.points)]
  },

  // Scoreboard `ttl.bounty` (done count) and exactly one stage `ttl.guild.<rank>`.
  sync(server, player, g) {
    var name = player.username
    var rank = String(this.rankOf(g).id).toLowerCase()
    this.ranks().forEach(r => {
      var stage = `ttl.guild.${String(r.id).toLowerCase()}`
      if (String(r.id).toLowerCase() === rank) {
        if (!player.stages.has(stage)) player.stages.add(stage)
      } else if (player.stages.has(stage)) {
        player.stages.remove(stage)
      }
    })
    server.runCommandSilent(`scoreboard players set ${name} ${this.BOUNTY} ${g.done}`)
  },

  // ---- progress ----

  landmarkSpot(server, name) {
    var at = String(server.persistentData.getString(`ttl.landmark.${name}.at`) || '')
    if (at) {
      var p = at.split(' ')
      return { x: Number(p[0]), z: Number(p[2]) }
    }
    var all = (TtlData.landmarks && TtlData.landmarks.landmark) || []
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].name) === String(name)) return { x: Number(all[i].x), z: Number(all[i].z) }
    }
    return null
  },

  near(server, player, name) {
    if (TtlLife.dimensionOf(player) !== TtlLife.OVERWORLD) return false
    var spot = this.landmarkSpot(server, name)
    if (!spot) return false
    var dx = player.getX() - spot.x
    var dz = player.getZ() - spot.z
    var r = Number(this.conf().guild.visit_radius)
    return dx * dx + dz * dz <= r * r
  },

  regionOf(player) {
    try {
      if (typeof TtlRep === 'undefined' || TtlLife.dimensionOf(player) !== TtlLife.OVERWORLD) return null
      return TtlRep.factionAt(Math.floor(player.getX()), Math.floor(player.getZ()))
    } catch (e) {
      return null
    }
  },

  progress(player, t, b) {
    if (b.kind === 'kill') return { have: Math.min(Number(t.got), b.count), need: b.count }
    if (b.kind === 'deliver') return { have: Math.min(Number(player.inventory.count(b.target)), b.count), need: b.count }
    return { have: t.got ? 1 : 0, need: 1 }
  },

  ready(player, t, b) {
    var p = this.progress(player, t, b)
    return p.have >= p.need
  },

  // Samples kills and visits for one player (every guild.poll_ticks, and by /ttl guild sample).
  sample(server, player) {
    var g = this.read(player)
    if (this.prune(server, g) > 0) this.write(player, g)
    var keys = Object.keys(g.taken)
    if (keys.length === 0) return 0
    var changed = false
    var self = this
    var region = null
    keys.forEach(key => {
      var t = g.taken[key]
      var b = self.find(t.id)
      if (!b) return
      if (b.kind === 'kill') {
        var cur = self.killValue(server, player, b.target)
        var delta = cur - t.last
        if (delta !== 0) {
          t.last = cur
          changed = true
          if (delta > 0) {
            if (b.region && region === null) region = self.regionOf(player) || ''
            if (!b.region || region === String(b.region)) t.got += delta
          }
        }
      } else if (b.kind === 'visit' && !t.got && self.near(server, player, b.target)) {
        t.got = 1
        changed = true
      }
      if (!t.told && self.ready(player, t, b) && b.kind !== 'deliver') {
        t.told = 1
        changed = true
        player.tell(Text.gold(`Free Guild: "${b.title}" is done. Report to the guild desk (/ttl guild turnin).`))
      }
    })
    if (changed) this.write(player, g)
    return keys.length
  },

  // ---- actions (they throw a message for the player when something is not allowed) ----

  take(server, player, ref, giver) {
    this.requireLife2(player)
    var e = this.entry(server, ref, giver)
    if (!e) throw `no such bounty on the board: ${ref}`
    var g = this.read(player)
    this.prune(server, g)
    var key = this.keyOf(e)
    if (g.taken[key]) throw `you already accepted "${e.b.title}"`
    if (g.hist.indexOf(key) >= 0) throw `you already completed "${e.b.title}" this ${e.period === 'daily' ? 'day' : 'week'}`
    if (this.rankIndexForPoints(g.points) < this.rankIndexOf(e.b.min_rank)) throw `"${e.b.title}" needs guild rank ${e.b.min_rank}`
    var max = Number(this.conf().guild.max_active)
    if (Object.keys(g.taken).length >= max) throw `you already carry ${max} bounties: hand one in or /ttl guild abandon it`
    var t = { id: String(e.b.id), period: e.period, stamp: e.stamp, got: 0, last: 0, told: 0 }
    if (e.b.kind === 'kill') t.last = this.killValue(server, player, e.b.target)
    g.taken[key] = t
    this.write(player, g)
    return e
  },

  abandon(server, player, ref) {
    this.requireLife2(player)
    var g = this.read(player)
    this.prune(server, g)
    var e = this.entry(server, ref)
    var key = e ? this.keyOf(e) : null
    if (!key || !g.taken[key]) throw `you have not accepted ${ref}`
    delete g.taken[key]
    this.write(player, g)
    return e
  },

  complete(server, player, g, key, b) {
    var rw = b.reward
    var coins = TtlEcon.pay(server, player, rw.coins, `bounty:${b.id}`)
    var rep = rw.rep || {}
    Object.keys(rep).forEach(f => {
      try {
        if (typeof TtlRep !== 'undefined') TtlRep.add(server, player, f, rep[f], `bounty ${b.id}`)
      } catch (e) {
        console.error(`[ttl] guild: reputation for ${b.id} (${f}) failed: ${e}`)
      }
    })
    var before = this.rankIndexForPoints(g.points)
    g.points += b.points
    g.done += 1
    g.hist.push(key)
    delete g.taken[key]
    var after = this.rankIndexForPoints(g.points)
    this.write(player, g)
    this.sync(server, player, g)
    console.info(`[ttl] guild: ${player.username} completed ${b.id}: ${coins} bronze, +${b.points} points (${g.points}, rank ${this.rankOf(g).id})`)
    player.tell(Text.green(`Free Guild: "${b.title}" complete. Paid ${TtlEcon.text(rw.coins)}.`))
    if (after > before) this.rankUp(server, player, after)
  },

  rankUp(server, player, index) {
    var rank = this.ranks()[index]
    player.tell(Text.gold(`Free Guild: you are now rank ${rank.id}, ${rank.title}.`))
    try {
      var announce = this.rankIndexOf(this.conf().guild.announce_rank)
      if (index >= announce && typeof TtlDiscord !== 'undefined' && !TtlDiscord.isBot(player.username)) {
        TtlDiscord.post(server, `${TtlDiscord.name(player.username)} reached rank **${rank.id}** (${rank.title}) in the Free Guild.`)
      }
    } catch (e) {
      console.warn(`[ttl] guild: rank announcement failed: ${e}`)
    }
  },

  // Hands in everything that is ready. Returns the number of bounties completed.
  // `giver` (optional) limits it to that giver's bounties: Fuze takes his contracts, a receptionist the desk's.
  turnin(server, player, giver) {
    this.requireLife2(player)
    var only = this.requireGiver(giver)
    var g = this.read(player)
    this.prune(server, g)
    var keys = Object.keys(g.taken)
    var count = 0
    var self = this
    keys.forEach(key => {
      var t = g.taken[key]
      var b = self.find(t.id)
      if (!b || (only && self.giverOf(b) !== only) || !self.ready(player, t, b)) return
      if (b.kind === 'deliver') server.runCommandSilent(`clear ${player.username} ${b.target} ${b.count}`)
      self.complete(server, player, g, key, b)
      count++
    })
    if (count === 0) {
      this.write(player, g)
      throw keys.length === 0 ? 'you have no accepted bounties (/ttl guild board)'
        : only ? `nothing of ${only === 'fuze' ? "Fuze's" : "the desk's"} is ready to hand in here (/ttl guild status)`
          : 'nothing is ready to hand in yet (/ttl guild status)'
    }
    return count
  },

  // Test/staff hook: forget the player's whole guild record, rank stage and counter.
  reset(server, player) {
    player.persistentData.remove(this.KEY)
    this.ranks().forEach(r => {
      var stage = `ttl.guild.${String(r.id).toLowerCase()}`
      if (player.stages.has(stage)) player.stages.remove(stage)
    })
    server.runCommandSilent(`scoreboard players set ${player.username} ${this.BOUNTY} 0`)
  },

  // ---- display ----

  slotStatus(player, g, e) {
    var key = this.keyOf(e)
    if (g.taken[key]) {
      var p = this.progress(player, g.taken[key], e.b)
      return `accepted ${p.have}/${p.need}`
    }
    if (g.hist.indexOf(key) >= 0) return 'done'
    if (this.rankIndexForPoints(g.points) < this.rankIndexOf(e.b.min_rank)) return `needs rank ${e.b.min_rank}`
    return 'open'
  },

  // `giver` filters the board and numbers the lines inside that giver's list (what `take <n> <giver>` expects).
  boardLines(server, player, giver) {
    var only = this.requireGiver(giver)
    var b = this.ensure(server)
    var g = this.read(player)
    this.prune(server, g)
    var title = only === 'fuze' ? `Fuze's contracts (rank ${this.conf().guild.fuze_min_rank} and up)`
      : only === 'desk' ? 'Free Guild desk board' : 'Free Guild board'
    var out = [`${title} (daily ${b.date}, week of ${b.week}). Your rank: ${this.rankOf(g).id}. /ttl guild take <number>${only ? ' ' + only : ''}`]
    var self = this
    var list = this.entries(server, only)
    list.forEach(e => {
      out.push(`${only ? e.local : e.slot}. [${e.period}, ${e.b.min_rank}] ${self.what(e.b)} (${e.b.title}): ${self.rewardText(e.b)} · ${self.slotStatus(player, g, e)}`)
    })
    if (list.length === 0) out.push('Nothing is posted here right now.')
    return out
  },

  statusLines(server, player) {
    var g = this.read(player)
    this.prune(server, g)
    var rank = this.rankOf(g)
    var idx = this.rankIndexForPoints(g.points)
    var next = this.ranks()[idx + 1]
    var out = [`Free Guild: rank ${rank.id} (${rank.title}), ${g.points} points${next ? `, ${next.points - g.points} to rank ${next.id}` : ', the highest rank'}; ${g.done} bounties done.`]
    var self = this
    Object.keys(g.taken).forEach(key => {
      var t = g.taken[key]
      var b = self.find(t.id)
      if (!b) return
      var p = self.progress(player, t, b)
      out.push(`- ${self.what(b)}: ${p.have}/${p.need}${p.have >= p.need ? ' (ready: /ttl guild turnin)' : ''}`)
    })
    return out
  },

  // ---- interim desks ----

  desks(server) {
    var raw = String(server.persistentData.getString(this.DESKS) || '')
    return raw ? JSON.parse(raw) : []
  },

  deskKey(x, y, z) {
    return `${x},${y},${z}`
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  try {
    TtlGuild.ensureObjectives(server)
    TtlGuild.ensure(server)
  } catch (e) {
    console.error(`[ttl] guild: setup failed: ${e}`)
  }
  var every = Math.max(20, Number(TtlGuild.conf().guild.poll_ticks))
  var loop = () => server.scheduleInTicks(every, () => {
    try {
      TtlGuild.ensure(server)
      server.getPlayerList().getPlayers().forEach(p => {
        try {
          if (TtlLife.phase(p) === 'life2') TtlGuild.sample(server, p)
        } catch (e) {
          console.error(`[ttl] guild: sampling ${p.username} failed: ${e}`)
        }
      })
    } catch (e) {
      console.error(`[ttl] guild: poll failed: ${e}`)
    }
    loop()
  })
  loop()
})

PlayerEvents.loggedIn(event => {
  var player = event.player
  try {
    if (TtlLife.phase(player) === 'life2') TtlGuild.sync(player.getServer(), player, TtlGuild.read(player))
  } catch (e) {
    console.error(`[ttl] guild: login sync for ${player.username} failed: ${e}`)
  }
})

// A registered desk shows the board (and what the player has accepted) when right-clicked with the main hand.
BlockEvents.rightClicked(event => {
  try {
    var player = event.player
    if (!player || String(event.hand) !== 'MAIN_HAND') return
    var server = player.getServer()
    var desks = TtlGuild.desks(server)
    if (desks.length === 0 || TtlLife.dimensionOf(player) !== TtlLife.OVERWORLD) return
    var b = event.block
    if (desks.indexOf(TtlGuild.deskKey(b.x, b.y, b.z)) < 0) return
    event.cancel()
    if (TtlLife.phase(player) !== 'life2') {
      player.tell(Text.gray('The Free Guild only takes on souls reborn in the Tensura world.'))
      return
    }
    TtlGuild.boardLines(server, player).concat(TtlGuild.statusLines(server, player)).forEach(line => player.tell(Text.of(line)))
  } catch (e) {
    console.error(`[ttl] guild: desk click failed: ${e}`)
  }
})
