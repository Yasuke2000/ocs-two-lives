// priority: 70
// The Artificer, core (design/architecture/paths-necro-artificer.md §3; WP-A1). Data: design/data/artifice.toml →
// TtlData.artifice. Commissions: artifice/commissions.js. Engraving, workshop recipes, the cursed whetstone and the
// schematics: artifice/workshop.js. Recipes and schematic drops: artifice/recipes.js. Commands: artifice/commands.js.
//
// R12: open to every Life 2 soul from the day it arrives (the charter needs a Workshop Bench and three schematics, no
// stage). R13: the honest road is the charter, commissions and the chisel; the dark shortcuts (cursed whetstone, stolen
// schematics) pay the five costs through TtlRoads.
//
// The maker's stamp. Tensura's Smithing Bench and Kiln fire no crafting event (javap 2.0.1.5: the bench's result slot
// only takes the ingredients in onTake; ItemEvents.crafted never sees it). Every [made_by] poll_ticks this file looks at
// the screen each Life 2 soul has open: while it is Tensura's SmithingBenchMenu or KilnMenu, what the soul carries is
// compared with what it carried when the screen opened (and once more when it closes, for the item on the cursor).
// New Smithing Bench products are stamped (item custom data `ttl_made_by` = UUID, `ttl_made_by_name`, a lore line) and
// earn craft points; new metal (a smithing product or a kiln ingot of a [points.craft] metal) counts for the firsts.
// The bench crafts straight from the inventory, so moving things around never looks like a craft there.
//
// Storage
//   player  ttl.artifice  JSON {rank, points, week, wk, craft, workshop: {x,y,z,dim}, metals: {metal: epoch},
//                         jobs: {"<date>:<id>": {id, at}}, done: ["<date>:<id>"], stole, last: {coins, id}, constructs: [],
//                         unlocked: []}   (constructs / unlocked: WP-A2/A3)
//   server  ttl.artifice.firsts   JSON {metal: {name, at}}  the server's first maker of each metal (never a test bot)
//           ttl.artifice.benches  JSON {"dim|x,y,z": {by: uuid, name, at}}  Workshop Benches placed (WP-A2: workshops)
//   stages  ttl.artifice.rank1..4 (all ranks reached)   scoreboard ttl.artifice = rank
//
// PUBLIC API (other packages call these guarded with typeof; `player` is a ServerPlayer)
//   TtlArtifice.rank(player) 0..4 · title(player) · record(player) the JSON above (read only) · caps(player)
//                         {constructs, muster} of the soul's rank (0/0 without a charter; WP-A2's construct caps)
//   TtlArtifice.addPoints(server, player, kind, n, reason)   pays artifice points within the weekly caps; `n` defaults
//                         to [points].<kind> (construct, engine, event ...). Returns the points paid. Kinds used here:
//                         craft, commission, engrave, metal. Rank-ups happen inside.
//   TtlArtifice.madeBy(server, stack) the maker's UUID on a stack, '' when none · isMine(server, player, stack)
//   TtlArtifice.stamp(server, player, stack, slot)   stamps a stack as made by the soul (radiant/test use)
//   TtlArtifice.cursed(stack) · tagOf(stack) · setTag(stack, key, value) · addLore(stack, text, color)
//   TtlArtifice.listen(fn(server, player, event, info))   events: 'charter', 'rank' {rank}, 'commission' {id, tier},
//                         'metal' {metal, server}. WP-A2/A3/X1 hook here (Hall, chronicle counts, relic unlocks).
//   TtlArtifice.benches(server)  the placed Workshop Benches (WP-A2 counts them in nation claims)
const TtlArtifice = {
  KEY: 'ttl.artifice',
  FIRSTS: 'ttl.artifice.firsts',
  BENCHES: 'ttl.artifice.benches',
  OBJ: 'ttl.artifice',
  STAMP: 'ttl_made_by',
  STAMP_NAME: 'ttl_made_by_name',
  CURSED: 'ttl_cursed',
  BENCH_MENU: /SmithingBenchMenu$/,
  KILN_MENU: /KilnMenu$/,
  DAY_MS: 86400000,
  smithOut: {},      // filled by artifice/recipes.js from Tensura's smithing_bench recipes (fallback: the metal rule)
  smithCount: 0,
  mem: {},           // uuid -> {cid, kind, have: {id: n}} while a bench or kiln screen is open
  flags: {},         // test hooks: uuid -> {anywhere: true}
  listeners: [],
  jv: undefined,

  conf() {
    return TtlData.artifice || {}
  },

  ranks() {
    return this.conf().rank || []
  },

  rankDef(n) {
    var all = this.ranks()
    for (var i = 0; i < all.length; i++) {
      if (Number(all[i].id) === Number(n)) return all[i]
    }
    return null
  },

  listen(fn) {
    this.listeners.push(fn)
  },

  emit(server, player, event, info) {
    this.listeners.forEach(fn => {
      try {
        fn(server, player, event, info || {})
      } catch (e) {
        console.error(`[ttl] artifice: a listener failed on ${event}: ${e}`)
      }
    })
  },

  isBot(player) {
    var name = String(player.username)
    try {
      if (typeof TtlDiscord !== 'undefined' && typeof TtlDiscord.isBot === 'function') return !!TtlDiscord.isBot(name)
    } catch (e) {
      // fall through
    }
    return /^TtlBot/.test(name)
  },

  weekKey() {
    try {
      if (typeof TtlEcon !== 'undefined') return TtlEcon.weekKey()
    } catch (e) {
      // fall through
    }
    var d = new Date()
    return new Date(d.getTime() - ((d.getUTCDay() + 6) % 7) * this.DAY_MS).toISOString().slice(0, 10)
  },

  dateKey() {
    return new Date().toISOString().slice(0, 10)
  },

  // ---- the record ------------------------------------------------------------------------------------------------

  read(player) {
    var raw = String(player.persistentData.getString(this.KEY))
    var s = {}
    try {
      s = raw ? JSON.parse(raw) : {}
    } catch (e) {
      console.error(`[ttl] artifice: ${player.username} ${this.KEY} unreadable, starting over: ${e}`)
    }
    s.rank = Number(s.rank || 0)
    s.points = Number(s.points || 0)
    s.week = Number(s.week || 0)
    s.craft = Number(s.craft || 0)
    s.wk = String(s.wk || '')
    s.metals = s.metals || {}
    s.jobs = s.jobs || {}
    s.done = s.done || []
    s.constructs = s.constructs || []
    s.unlocked = s.unlocked || []
    var wk = this.weekKey()
    if (s.wk !== wk) {
      s.wk = wk
      s.week = 0
      s.craft = 0
    }
    return s
  },

  write(player, s) {
    player.persistentData.putString(this.KEY, JSON.stringify(s))
  },

  record(player) {
    return this.read(player)
  },

  rank(player) {
    return this.read(player).rank
  },

  title(player) {
    var def = this.rankDef(this.rank(player))
    return def ? String(def.title) : ''
  },

  caps(player) {
    var def = this.rankDef(this.rank(player))
    return def ? { constructs: Number(def.constructs), muster: Number(def.muster) } : { constructs: 0, muster: 0 }
  },

  clear(server, player) {
    player.persistentData.remove(this.KEY)
    this.ranks().forEach(r => player.stages.remove(`ttl.artifice.rank${r.id}`))
    server.runCommandSilent(`scoreboard players set ${player.username} ${this.OBJ} 0`)
    delete this.mem[TtlLife.uuid(player)]
  },

  // ---- ranks and points ------------------------------------------------------------------------------------------

  meets(player, def) {
    var req = def.requires_any
    if (!req) return true
    var skills = req.skills || []
    if (skills.length > 0) {
      try {
        var held = typeof TtlManas !== 'undefined' ? TtlManas.uniques(player) : null
        if (held && skills.some(s => held.indexOf(String(s)) >= 0)) return true
      } catch (e) {
        console.warn(`[ttl] artifice: reading ${player.username}'s uniques failed: ${e}`)
      }
    }
    var bands = req.bands || {}
    return Object.keys(bands).some(f => {
      try {
        return typeof TtlRep !== 'undefined' && TtlRep.atLeast(player, f, String(bands[f]))
      } catch (e) {
        return false
      }
    })
  },

  // The rank the record has earned (never lower than the stored one; 0 stays 0 until the charter).
  earned(player, s) {
    if (s.rank < 1) return 0
    var best = s.rank
    var all = this.ranks()
    for (var i = 0; i < all.length; i++) {
      var r = all[i]
      if (Number(r.id) <= best) continue
      if (s.points < Number(r.points) || !this.meets(player, r)) break
      best = Number(r.id)
    }
    return best
  },

  sync(server, player, s) {
    var rank = s ? s.rank : this.rank(player)
    this.ranks().forEach(r => {
      var stage = `ttl.artifice.rank${r.id}`
      if (Number(r.id) <= rank) player.stages.add(stage)
      else player.stages.remove(stage)
    })
    server.runCommandSilent(`scoreboard players set ${player.username} ${this.OBJ} ${rank}`)
  },

  // Promotes the soul as far as its points and requirements allow; returns the new rank.
  refresh(server, player, s) {
    var own = !s
    s = s || this.read(player)
    var target = this.earned(player, s)
    while (s.rank < target) {
      s.rank++
      this.write(player, s)
      this.promoted(server, player, s.rank)
    }
    if (own) this.write(player, s)
    this.sync(server, player, s)
    return s.rank
  },

  promoted(server, player, rank) {
    var def = this.rankDef(rank)
    if (!def) return
    var name = String(player.username)
    console.info(`[ttl] artifice: ${name} is now rank ${rank}, ${def.title}`)
    player.tell(Text.gold(`Workshop: you are now a ${def.title}.`))
    this.addTitle(player, String(def.title))
    if (Number(def.renown) > 0) {
      try {
        if (typeof TtlRep !== 'undefined') TtlRep.addRenown(server, player, Number(def.renown), `artifice rank ${rank}`)
      } catch (e) {
        console.error(`[ttl] artifice: renown for ${name} failed: ${e}`)
      }
    }
    if (def.era_title) {
      try {
        if (typeof TtlEra !== 'undefined' && TtlEra.titleDef(def.era_title) && !this.eraTitleTaken(server, String(def.era_title))) {
          TtlEra.award(server, player, String(def.era_title))
        }
      } catch (e) {
        console.warn(`[ttl] artifice: era title ${def.era_title} for ${name} failed: ${e}`)
      }
    }
    if (def.announce && !this.isBot(player)) {
      try {
        if (typeof TtlDiscord !== 'undefined') TtlDiscord.post(server, `${TtlDiscord.name(name)} is now a **${def.title}**.`)
      } catch (e) {
        console.warn(`[ttl] artifice: rank announcement failed: ${e}`)
      }
    }
    this.chronicle(server, 'artifice_rank', player, { rank: rank })
    this.emit(server, player, 'rank', { rank: rank })
  },

  // One era title per era for the whole server (the first Grand Artificer).
  eraTitleTaken(server, id) {
    var all = TtlEra.titles(server)
    return Object.keys(all).some(k => (all[k] || []).indexOf(id) >= 0)
  },

  addTitle(player, title) {
    var raw = String(player.persistentData.getString('ttl.titles') || '')
    var list = raw ? raw.split(',') : []
    if (list.indexOf(title) >= 0) return
    list.push(title)
    player.persistentData.putString('ttl.titles', list.join(','))
  },

  chronicle(server, kind, player, info) {
    try {
      if (typeof TtlChronicle !== 'undefined' && typeof TtlChronicle.note === 'function') {
        var extra = { system: 'artifice' }
        Object.keys(info || {}).forEach(k => { extra[k] = info[k] })
        TtlChronicle.note(server, kind, player, extra)
      }
    } catch (e) {
      console.warn(`[ttl] artifice: chronicle ${kind} failed: ${e}`)
    }
  },

  addPoints(server, player, kind, n, reason) {
    if (TtlLife.phase(player) !== 'life2') return 0
    var pts = this.conf().points || {}
    var want = n === undefined || n === null ? Number(pts[kind] || 0) : Number(n)
    if (!(want > 0)) return 0
    var s = this.read(player)
    if (s.rank < 1) return 0
    var room = Number(pts.weekly_cap) - s.week
    if (kind === 'craft') room = Math.min(room, Number(pts.craft_weekly_cap) - s.craft)
    var gain = Math.max(0, Math.min(want, room))
    if (gain <= 0) {
      console.info(`[ttl] artifice: ${player.username} ${kind} points capped this week`)
      return 0
    }
    s.points += gain
    s.week += gain
    if (kind === 'craft') s.craft += gain
    this.write(player, s)
    console.info(`[ttl] artifice: ${player.username} +${gain} points for ${reason || kind} (${s.points}, week ${s.week})`)
    this.refresh(server, player, s)
    return gain
  },

  setPoints(server, player, n) {
    var s = this.read(player)
    s.points = Math.max(0, Math.floor(Number(n)))
    this.write(player, s)
    return this.refresh(server, player, s)
  },

  // ---- the charter -----------------------------------------------------------------------------------------------

  // Schematic ids the soul knows (Tensura's per-player storage) or carries, distinct.
  schematics(player) {
    var ids = {}
    try {
      var known = Java.loadClass('io.github.manasmods.tensura.storage.TensuraStorages').getPlayerDataFrom(player).getKnownSchematics()
      known.forEach(k => { ids[String(k)] = true })
    } catch (e) {
      console.warn(`[ttl] artifice: Tensura's known schematics unreadable, counting carried ones only: ${e}`)
    }
    var inv = player.getInventory()
    for (var i = 0; i < inv.getContainerSize(); i++) {
      var st = inv.getItem(i)
      if (!st.isEmpty() && /^tensura:.*schematic$/.test(String(st.id))) ids[String(st.id)] = true
    }
    return Object.keys(ids)
  },

  checkCharter(player) {
    if (TtlLife.phase(player) !== 'life2') return 'life2only'
    if (this.rank(player) > 0) return 'already chartered'
    if (!TtlWorkshop.near(player, 'bench')) return 'not at a Workshop Bench'
    var need = Number((this.conf().charter || {}).schematics || 3)
    var have = this.schematics(player).length
    if (have < need) return `needs ${need} schematics (you know or carry ${have})`
    return ''
  },

  charter(server, player) {
    var why = this.checkCharter(player)
    if (why) throw why
    var s = this.read(player)
    s.rank = 1
    var bench = TtlWorkshop.near(player, 'bench')
    if (bench) s.workshop = { x: bench.x, y: bench.y, z: bench.z, dim: TtlLife.dimensionOf(player) }
    this.write(player, s)
    var item = String((this.conf().charter || {}).item || 'ttl:artificer_charter')
    TtlCmd.run(server, `give ${player.username} ${item}`)
    this.promoted(server, player, 1)
    this.refresh(server, player, s)
    this.chronicle(server, 'artifice_charter', player, {})
    this.emit(server, player, 'charter', {})
    player.tell(Text.gold('Workshop: your charter is signed. Commissions, the chisel and the Workshop menu are open to you.'))
    return s
  },

  // ---- components: the stamp and the curse -------------------------------------------------------------------------

  java() {
    if (this.jv !== undefined) return this.jv
    try {
      this.jv = {
        DC: Java.loadClass('net.minecraft.core.component.DataComponents'),
        CustomData: Java.loadClass('net.minecraft.world.item.component.CustomData'),
        ItemLore: Java.loadClass('net.minecraft.world.item.component.ItemLore'),
        Component: Java.loadClass('net.minecraft.network.chat.Component'),
        Style: Java.loadClass('net.minecraft.network.chat.Style'),
        ChatFormatting: Java.loadClass('net.minecraft.ChatFormatting'),
        CompoundTag: Java.loadClass('net.minecraft.nbt.CompoundTag')
      }
    } catch (e) {
      console.error(`[ttl] artifice: item component classes unavailable, no maker's stamps: ${e}`)
      this.jv = null
    }
    return this.jv
  },

  // A copy of the stack's custom data (CompoundTag), or null.
  tagOf(stack) {
    if (!stack || stack.isEmpty()) return null
    var j = this.java()
    if (!j) return null
    try {
      var cd = stack.get(j.DC.CUSTOM_DATA)
      return cd ? cd.copyTag() : null
    } catch (e) {
      console.warn(`[ttl] artifice: reading custom data failed: ${e}`)
      return null
    }
  },

  setTag(stack, key, value) {
    var j = this.java()
    if (!j) return false
    var tag = this.tagOf(stack) || new j.CompoundTag()
    tag.putString(String(key), String(value))
    stack.set(j.DC.CUSTOM_DATA, j.CustomData.of(tag))
    return true
  },

  addLore(stack, text, color) {
    var j = this.java()
    if (!j) return false
    try {
      var lore = stack.get(j.DC.LORE) || j.ItemLore.EMPTY
      var style = j.Style.EMPTY.withItalic(false).withColor(color === 'red' ? j.ChatFormatting.DARK_RED : j.ChatFormatting.GRAY)
      stack.set(j.DC.LORE, lore.withLineAdded(j.Component.literal(String(text)).setStyle(style)))
      return true
    } catch (e) {
      console.warn(`[ttl] artifice: lore line failed: ${e}`)
      return false
    }
  },

  madeBy(server, stack) {
    var tag = this.tagOf(stack)
    return tag && tag.contains(this.STAMP) ? String(tag.getString(this.STAMP)) : ''
  },

  isMine(server, player, stack) {
    return this.madeBy(server, stack) === TtlLife.uuid(player)
  },

  cursed(stack) {
    var tag = this.tagOf(stack)
    return !!(tag && tag.contains(this.CURSED))
  },

  stamp(server, player, stack, slot) {
    if (!stack || stack.isEmpty() || this.madeBy(server, stack)) return false
    var name = String(player.username)
    try {
      if (!this.setTag(stack, this.STAMP, TtlLife.uuid(player))) throw 'no component classes'
      this.setTag(stack, this.STAMP_NAME, name)
      this.addLore(stack, String((this.conf().made_by || {}).lore || 'Made by {name}').replace('{name}', name))
      return true
    } catch (e) {
      // Fallback: the same through /item (inline modifier, 1.21 syntax), when the slot is known.
      console.warn(`[ttl] artifice: stamping ${stack.id} for ${name} through the API failed (${e}), trying /item`)
      if (slot === undefined || slot === null || slot > 35) return false
      var tag = `{${this.STAMP}:"${TtlLife.uuid(player)}",${this.STAMP_NAME}:"${name}"}`
      return TtlCmd.run(server, `item modify entity ${name} container.${slot} {function:"minecraft:set_custom_data",tag:'${tag}'}`) > 0
    }
  },

  // ---- what the Smithing Bench and the Kiln make --------------------------------------------------------------------

  metals() {
    return Object.keys((this.conf().points || {}).craft || {})
  },

  metalOf(id) {
    var m = /^tensura:([a-z_]+?)_(.+)$/.exec(String(id))
    if (!m) return ''
    var all = this.metals()
    // Longest metal name first (pure_magisteel before magisteel-like prefixes).
    var hit = ''
    all.forEach(metal => {
      if (String(id).indexOf(`tensura:${metal}_`) === 0 && metal.length > hit.length) hit = metal
    })
    return hit
  },

  isSmithOut(id) {
    id = String(id)
    if (this.smithCount > 0) return !!this.smithOut[id]
    return !!this.metalOf(id) && !/_(ingot|nugget|block|bone_golem|gear_schematic)$/.test(id)
  },

  isMetalIngot(id) {
    var metal = this.metalOf(id)
    return !!metal && String(id) === `tensura:${metal}_ingot`
  },

  counts(player, kind) {
    var out = {}
    var inv = player.getInventory()
    for (var i = 0; i < inv.getContainerSize(); i++) {
      var st = inv.getItem(i)
      if (st.isEmpty()) continue
      var id = String(st.id)
      if (kind === 'bench' ? this.isSmithOut(id) : this.isMetalIngot(id)) out[id] = (out[id] || 0) + Number(st.count)
    }
    return out
  },

  // n new items of `id` came out of the bench (kind 'bench') or the kiln (kind 'kiln').
  made(server, player, id, n, kind) {
    var metal = this.metalOf(id)
    if (kind === 'bench') {
      var left = n
      var inv = player.getInventory()
      for (var i = 0; i < inv.getContainerSize() && left > 0; i++) {
        var st = inv.getItem(i)
        if (st.isEmpty() || String(st.id) !== id || this.madeBy(server, st)) continue
        if (this.stamp(server, player, st, i)) left -= Number(st.count)
      }
      var per = Number((((this.conf().points || {}).craft) || {})[metal] || 0)
      if (per > 0) this.addPoints(server, player, 'craft', per * n, `made ${n} ${id}`)
      console.info(`[ttl] artifice: ${player.username} made ${n} ${id} at the Smithing Bench`)
    }
    if (metal) this.metalFirst(server, player, metal)
  },

  metalFirst(server, player, metal) {
    var s = this.read(player)
    if (s.metals[metal]) return
    s.metals[metal] = Date.now()
    this.write(player, s)
    var pts = this.conf().points || {}
    this.addPoints(server, player, 'metal', Number(pts.metal_first_soul || 0), `first ${metal}`)
    var serverFirst = false
    if (!this.isBot(player)) {
      var firsts = this.firsts(server)
      if (!firsts[metal]) {
        firsts[metal] = { name: String(player.username), at: Date.now() }
        server.persistentData.putString(this.FIRSTS, JSON.stringify(firsts))
        serverFirst = true
        this.addPoints(server, player, 'metal', Number(pts.metal_first_server || 0), `server first ${metal}`)
        this.chronicle(server, 'first_craft', player, { metal: metal, first: `craft.${metal}` })
        try {
          if (typeof TtlDiscord !== 'undefined') TtlDiscord.post(server, `${TtlDiscord.name(String(player.username))} is the first to work **${metal.replace(/_/g, ' ')}** in this world.`)
        } catch (e) {
          console.warn(`[ttl] artifice: first-metal line failed: ${e}`)
        }
      }
    }
    this.emit(server, player, 'metal', { metal: metal, server: serverFirst })
  },

  firsts(server) {
    try {
      return JSON.parse(String(server.persistentData.getString(this.FIRSTS)) || '{}')
    } catch (e) {
      return {}
    }
  },

  // New items since the last look; `have` follows the inventory down (things put into the kiln) and up (made).
  look(server, player, m) {
    var cur = this.counts(player, m.kind)
    var self = this
    Object.keys(cur).forEach(id => {
      var was = Number(m.have[id] || 0)
      if (cur[id] > was) self.made(server, player, id, cur[id] - was, m.kind)
    })
    m.have = cur
  },

  poll(server) {
    var self = this
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        if (TtlLife.phase(p) !== 'life2') return
        var uid = TtlLife.uuid(p)
        var menu = p.containerMenu
        // Rhino refuses getClass(); a menu without its own toString prints as <class name>@<hash>.
        var cls = menu ? String(menu).split('@')[0] : ''
        var kind = self.BENCH_MENU.test(cls) ? 'bench' : self.KILN_MENU.test(cls) ? 'kiln' : ''
        var m = self.mem[uid]
        if (m && (!kind || m.cid !== Number(menu.containerId))) {
          // Closed (or another bench screen): one last look catches the item that was on the cursor.
          self.look(server, p, m)
          delete self.mem[uid]
          m = null
        }
        if (!kind) return
        if (!m) {
          self.mem[uid] = { cid: Number(menu.containerId), kind: kind, have: self.counts(p, kind) }
          return
        }
        self.look(server, p, m)
      } catch (e) {
        console.error(`[ttl] artifice: maker's stamp poll for ${p.username} failed: ${e}`)
      }
    })
  },

  // ---- Workshop Benches in the world -------------------------------------------------------------------------------

  benches(server) {
    try {
      return JSON.parse(String(server.persistentData.getString(this.BENCHES)) || '{}')
    } catch (e) {
      return {}
    }
  },

  benchKey(dim, x, y, z) {
    return `${dim}|${x},${y},${z}`
  },

  noteBench(server, player, dim, x, y, z, placed) {
    var all = this.benches(server)
    var key = this.benchKey(dim, x, y, z)
    if (placed) all[key] = { by: player ? TtlLife.uuid(player) : '', name: player ? String(player.username) : '', at: Date.now() }
    else delete all[key]
    server.persistentData.putString(this.BENCHES, JSON.stringify(all))
  },

  // ---- the curse on hit ----------------------------------------------------------------------------------------------

  curseHit(server, attacker, victim) {
    var conf = this.conf().curse || {}
    if (Math.random() >= Number(conf.chance || 0)) return
    ;(conf.effects || []).forEach(ef => {
      var ticks = Number(ef.seconds) * 20
      try {
        victim.potionEffects.add(String(ef.id), ticks, Number(ef.amplifier), false, true)
      } catch (e) {
        TtlCmd.run(server, `effect give ${victim.uuid} ${ef.id} ${ef.seconds} ${ef.amplifier}`)
      }
    })
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  try {
    server.runCommandSilent(`scoreboard objectives add ${TtlArtifice.OBJ} dummy`)
  } catch (e) {
    console.warn(`[ttl] artifice: scoreboard ${TtlArtifice.OBJ} not created: ${e}`)
  }
  var every = Math.max(1, Number((TtlArtifice.conf().made_by || {}).poll_ticks || 5))
  var loop = () => server.scheduleInTicks(every, () => {
    try {
      TtlArtifice.poll(server)
    } catch (e) {
      console.error(`[ttl] artifice: poll failed: ${e}`)
    }
    loop()
  })
  loop()
  console.info(`[ttl] artifice: maker's stamp poll every ${every} ticks (${TtlArtifice.smithCount} Smithing Bench products known)`)
})

PlayerEvents.loggedIn(event => {
  var player = event.player
  try {
    if (TtlLife.phase(player) === 'life2' && TtlArtifice.rank(player) > 0) TtlArtifice.refresh(player.getServer(), player)
  } catch (e) {
    console.error(`[ttl] artifice: login sync for ${player.username} failed: ${e}`)
  }
})

// A cursed blade's hit: Tensura's Fear and Wither, at [curse] chance.
EntityEvents.afterHurt(event => {
  try {
    var attacker = event.source.actual
    if (!attacker || !attacker.isPlayer()) return
    var stack = attacker.getMainHandItem()
    if (stack.isEmpty() || !TtlArtifice.cursed(stack)) return
    TtlArtifice.curseHit(attacker.getServer(), attacker, event.entity)
  } catch (e) {
    console.error(`[ttl] artifice: cursed hit failed: ${e}`)
  }
})

// Workshop Benches placed and broken (WP-A2 counts workshops in nation claims).
BlockEvents.placed('ttl:workshop_bench', event => {
  try {
    var b = event.block
    var e = event.entity
    var p = e && String(e.type) === 'minecraft:player' ? e : null
    TtlArtifice.noteBench(b.level.getServer(), p, String(b.level.dimension), b.x, b.y, b.z, true)
  } catch (e) {
    console.error(`[ttl] artifice: bench placement note failed: ${e}`)
  }
})

BlockEvents.broken('ttl:workshop_bench', event => {
  try {
    var b = event.block
    TtlArtifice.noteBench(b.level.getServer(), null, String(b.level.dimension), b.x, b.y, b.z, false)
  } catch (e) {
    console.error(`[ttl] artifice: bench removal note failed: ${e}`)
  }
})
