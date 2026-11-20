// priority: 70
// Merit-lite (owner decision O5: merit now, charters / likes / Builder's Economy as a later sprint; numbers in
// design/data/economy.toml [merit]). Placing an infrastructure block (merit.blocks) inside a PUBLIC WORKS chunk earns
// merit; every 100 merit pays merit.rep_per_100 reputation with the faction whose canon region the chunk lies in
// (TtlRep.add, only when the reputation package is loaded), and total merit >= merit.builder_at gives the Builder title
// (stage `ttl.title.builder`, also added to persistentData `ttl.titles` as a comma-separated list).
//
// Public Works chunks: a Life 2 player marks the chunk they stand in with /ttl merit works mark (at most
// merit.works_per_player each). This stands in for the nations package: the nation design (S4) calls them "the nation's
// Public Works chunk" and FTB Chunks claims are not readable from here yet (verify `FTBChunksAPI` from JS), so until
// then any chunk can be marked and the caps below are what keep it honest: merit.weekly_cap per player per week and
// merit.chunk_weekly_cap per chunk per player per week. Server persistentData `ttl.merit.works` = {chunkKey: {by, faction}}
// (chunkKey = "<dimension>|<chunkX>,<chunkZ>"); player persistentData `ttl.merit` = {total, week, wk, paid, chunks}.
//
// Only the Tensura overworld counts. BlockEvents.placed fires for player placement; /ttl merit test <p> <block> runs the
// same code path for the bot tests.
const TtlMerit = {
  KEY: 'ttl.merit',
  WORKS: 'ttl.merit.works',

  conf() {
    return TtlData.economy.merit
  },

  isMerit(id) {
    return this.conf().blocks.map(b => String(b)).indexOf(String(id)) >= 0
  },

  chunkKey(dim, x, z) {
    return `${dim}|${x >> 4},${z >> 4}`
  },

  works(server) {
    var raw = String(server.persistentData.getString(this.WORKS) || '')
    return raw ? JSON.parse(raw) : {}
  },

  saveWorks(server, w) {
    server.persistentData.putString(this.WORKS, JSON.stringify(w))
  },

  read(player) {
    var raw = String(player.persistentData.getString(this.KEY) || '')
    var m = raw ? JSON.parse(raw) : {}
    m.total = m.total || 0
    m.paid = m.paid || 0
    m.week = m.week || 0
    m.wk = m.wk || ''
    m.chunks = m.chunks || {}
    var wk = TtlEcon.weekKey()
    if (m.wk !== wk) {
      m.wk = wk
      m.week = 0
      m.chunks = {}
    }
    return m
  },

  write(player, m) {
    player.persistentData.putString(this.KEY, JSON.stringify(m))
  },

  // The faction ID of the canon region at x, z ('' for none). TtlRep.factionAt returns the faction table, not the id.
  faction(x, z) {
    try {
      var f = typeof TtlRep !== 'undefined' ? TtlRep.factionAt(x, z) : null
      return f ? String(f.id) : ''
    } catch (e) {
      return ''
    }
  },

  // The faction a Public Works record pays: its stored id, or (an old record kept the whole faction table, a
  // string like "[object Object]" or nothing) the region of the chunk the block went into.
  worksFaction(rec, x, z) {
    var f = rec ? rec.faction : null
    if (f && typeof f === 'object') f = f.id
    f = f ? String(f) : ''
    if (f && typeof TtlRep !== 'undefined' && TtlRep.faction(f)) return f
    return this.faction(x, z)
  },

  mark(server, player) {
    TtlGuild.requireLife2(player)
    var dim = TtlLife.dimensionOf(player)
    if (dim !== TtlLife.OVERWORLD) throw 'Public Works can only be marked in the Tensura overworld'
    var x = Math.floor(player.getX())
    var z = Math.floor(player.getZ())
    var key = this.chunkKey(dim, x, z)
    var w = this.works(server)
    var me = TtlLife.uuid(player)
    if (w[key] && w[key].by === me) return { key: key, faction: this.worksFaction(w[key], x, z) || null, already: true }
    if (w[key]) throw 'this chunk is already Public Works of someone else'
    var mine = Object.keys(w).filter(k => w[k].by === me).length
    var max = Number(this.conf().works_per_player)
    if (mine >= max) throw `you already keep ${max} Public Works chunks (/ttl merit works unmark first)`
    var f = this.faction(x, z)
    w[key] = { by: me, faction: f }
    this.saveWorks(server, w)
    return { key: key, faction: f || null }
  },

  unmark(server, player) {
    var key = this.chunkKey(TtlLife.dimensionOf(player), Math.floor(player.getX()), Math.floor(player.getZ()))
    var w = this.works(server)
    if (!w[key] || (w[key].by !== TtlLife.uuid(player) && !player.hasPermissions(2))) throw 'this chunk is not one of your Public Works'
    delete w[key]
    this.saveWorks(server, w)
    return key
  },

  // One counted block. Returns the merit gained (0 when nothing counted).
  place(server, player, id, x, z) {
    if (TtlLife.phase(player) !== 'life2' || !this.isMerit(id)) return 0
    var dim = TtlLife.dimensionOf(player)
    if (dim !== TtlLife.OVERWORLD) return 0
    var key = this.chunkKey(dim, x, z)
    var w = this.works(server)
    if (!w[key]) return 0
    var c = this.conf()
    var m = this.read(player)
    var room = Math.min(Number(c.weekly_cap) - m.week, Number(c.chunk_weekly_cap) - (m.chunks[key] || 0))
    var gain = Math.min(Number(c.per_block), room)
    if (gain <= 0) return 0
    m.total += gain
    m.week += gain
    m.chunks[key] = (m.chunks[key] || 0) + gain
    var owed = Math.floor(m.total / 100) - m.paid
    if (owed > 0) {
      m.paid += owed
      var f = this.worksFaction(w[key], x, z)
      var rep = owed * Number(c.rep_per_100)
      try {
        if (f && typeof TtlRep !== 'undefined') TtlRep.add(server, player, f, rep, 'merit')
      } catch (e) {
        console.error(`[ttl] merit: reputation for ${player.username} (${f}) failed: ${e}`)
      }
      player.tell(Text.gold(`Merit: your work for the common good earns ${rep} reputation${f ? ` with ${f}` : ''}.`))
    }
    this.write(player, m)
    this.checkBuilder(player, m)
    return gain
  },

  checkBuilder(player, m) {
    if (m.total < Number(this.conf().builder_at) || player.stages.has('ttl.title.builder')) return
    player.stages.add('ttl.title.builder')
    var raw = String(player.persistentData.getString('ttl.titles') || '')
    var list = raw ? raw.split(',') : []
    if (list.indexOf('Builder') < 0) {
      list.push('Builder')
      player.persistentData.putString('ttl.titles', list.join(','))
    }
    player.tell(Text.gold('You are known as a Builder: the settlements remember the roads and walls you raised.'))
    console.info(`[ttl] merit: ${player.username} earned the Builder title (${m.total} merit)`)
  },

  // Test/staff hook: forget the player's merit, their Public Works chunks and the Builder title.
  reset(server, player) {
    var me = TtlLife.uuid(player)
    var w = this.works(server)
    Object.keys(w).forEach(k => {
      if (w[k].by === me) delete w[k]
    })
    this.saveWorks(server, w)
    player.persistentData.remove(this.KEY)
    if (player.stages.has('ttl.title.builder')) player.stages.remove('ttl.title.builder')
  },

  lines(server, player) {
    var m = this.read(player)
    var c = this.conf()
    var w = this.works(server)
    var me = TtlLife.uuid(player)
    var mine = Object.keys(w).filter(k => w[k].by === me)
    return [
      `Merit: ${m.total} total, ${m.week}/${c.weekly_cap} this week; ${c.rep_per_100} reputation per 100; Builder at ${c.builder_at}.`,
      `Public Works you keep (${mine.length}/${c.works_per_player}): ${mine.join('; ') || 'none (stand in a chunk, /ttl merit works mark)'}`
    ]
  }
}

BlockEvents.placed(event => {
  try {
    var entity = event.entity
    if (!entity || String(entity.type) !== 'minecraft:player') return
    var b = event.block
    TtlMerit.place(entity.getServer(), entity, String(b.id), b.x, b.z)
  } catch (e) {
    console.error(`[ttl] merit: placed check failed: ${e}`)
  }
})
