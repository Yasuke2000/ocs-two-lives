// priority: 66
// The workshop's actions (design/architecture/paths-necro-artificer.md §3.4, §3.6; artifice.toml): the Workshop menu, the
// engraving chisel (the honest road), workshop recipes (rank-gated, made through the menu), the cursed whetstone (the dark
// shortcut), schematics bought from Dwargon (honest) or stolen from its smithy (dark). Every dark act pays through TtlRoads
// (roads.toml artifice.engrave, artifice.schematic). Each action has a check(...) that returns '' or the reason, so tests
// and menus can ask without side effects (`ttl artifice expect <p> try_<action> ...`).
//
// PUBLIC API
//   TtlWorkshop.near(player, 'bench' | 'altar')    {x, y, z} of a Workshop Bench / Bone Altar within [bench] reach, or null
//   TtlWorkshop.menu(server, player)               the Workshop screen (ttl-portals /ttlmenu)
//   TtlWorkshop.checkEngrave/engrave(server, player, id) · checkMake/make(server, player, id) · checkCurse/curse
//   TtlWorkshop.checkBuy/buy(server, player) · checkSteal/steal(server, player)
const TtlWorkshop = {
  channels: {},   // uuid -> {x, y, z, until} while a theft is being channelled

  conf() {
    return TtlArtifice.conf()
  },

  flag(player, name) {
    var f = TtlArtifice.flags[TtlLife.uuid(player)] || {}
    return !!f[name]
  },

  near(player, what) {
    var id = what === 'altar' ? 'ttl:bone_altar' : String((this.conf().bench || {}).block || 'ttl:workshop_bench')
    var r = Number((this.conf().bench || {}).reach || 4)
    var level = player.level
    var px = Math.floor(player.getX())
    var py = Math.floor(player.getY())
    var pz = Math.floor(player.getZ())
    for (var dy = -2; dy <= 2; dy++) {
      for (var dx = -r; dx <= r; dx++) {
        for (var dz = -r; dz <= r; dz++) {
          if (String(level.getBlock(px + dx, py + dy, pz + dz).id) === id) return { x: px + dx, y: py + dy, z: pz + dz }
        }
      }
    }
    return null
  },

  count(player, id) {
    var n = 0
    var inv = player.getInventory()
    for (var i = 0; i < inv.getContainerSize(); i++) {
      var st = inv.getItem(i)
      if (!st.isEmpty() && String(st.id) === String(id)) n += Number(st.count)
    }
    return n
  },

  missing(player, table) {
    var out = []
    var self = this
    Object.keys(table || {}).forEach(id => {
      var have = self.count(player, id)
      if (have < Number(table[id])) out.push(`${Number(table[id]) - have} x ${TtlCommission.pretty(id)}`)
    })
    return out
  },

  take(server, player, table) {
    Object.keys(table || {}).forEach(id => {
      TtlCmd.run(server, `clear ${player.username} ${id} ${Number(table[id])}`)
    })
  },

  base(player) {
    if (TtlLife.phase(player) !== 'life2') return 'life2only'
    return ''
  },

  // ---- engraving (rank 2+, own work, the chisel) -----------------------------------------------------------------------

  engraving(id) {
    var list = this.conf().engraving || []
    for (var i = 0; i < list.length; i++) {
      if (String(list[i].id) === String(id)) return list[i]
    }
    return null
  },

  checkEngrave(server, player, id) {
    var why = this.base(player)
    if (why) return why
    var e = this.engraving(id)
    if (!e) return `no engraving ${id}`
    var rank = TtlArtifice.rank(player)
    var def = TtlArtifice.rankDef(rank)
    if (!def || !def.engrave) return 'engraving needs rank 2 (Artisan)'
    if (rank < Number(e.rank)) return `${TtlCommission.pretty(id)} needs rank ${e.rank}`
    if (this.count(player, (this.conf().engrave || {}).chisel || 'ttl:engraving_chisel') < 1) return 'needs an Engraving Chisel'
    if (!this.near(player, 'bench')) return 'not at a Workshop Bench'
    var hand = player.getMainHandItem()
    if (hand.isEmpty()) return 'hold the item to engrave in your main hand'
    if (!TtlArtifice.isMine(server, player, hand)) return 'the chisel only answers to your own work (the item must carry your maker\'s stamp)'
    var cost = e.cost || {}
    var short = this.missing(player, cost.items)
    if (short.length) return `missing ${short.join(', ')}`
    if (cost.coins && !TtlEcon.canPay(player, cost.coins)) return `needs ${TtlEcon.text(cost.coins)}`
    return ''
  },

  engrave(server, player, id) {
    var why = this.checkEngrave(server, player, id)
    if (why) throw why
    var e = this.engraving(id)
    // /enchant checks that the engraving fits the item and does not clash with one it already carries.
    var ok = TtlCmd.run(server, `enchant ${player.username} ${e.id} 1`)
    if (!ok) throw `${TtlCommission.pretty(e.id)} does not take on this item (wrong kind of item, or it already carries an engraving)`
    var cost = e.cost || {}
    this.take(server, player, cost.items)
    if (cost.coins) TtlEcon.charge(server, player, cost.coins, `engrave:${e.id}`)
    try {
      if (typeof TtlRoads !== 'undefined') TtlRoads.pay(server, player, { id: 'artifice.engrave', road: 'grey', reason: `engrave ${e.id}` })
    } catch (err) {
      console.warn(`[ttl] artifice: roads note for the engraving failed: ${err}`)
    }
    TtlArtifice.addPoints(server, player, 'engrave', null, `engrave ${e.id}`)
    console.info(`[ttl] artifice: ${player.username} engraved ${e.id} on ${player.getMainHandItem().id}`)
    player.tell(Text.green(`Workshop: the chisel bites clean. ${TtlCommission.pretty(e.id)} is engraved.`))
  },

  // ---- workshop recipes --------------------------------------------------------------------------------------------------

  recipe(id) {
    var list = this.conf().recipe || []
    for (var i = 0; i < list.length; i++) {
      if (String(list[i].id) === String(id)) return list[i]
    }
    return null
  },

  checkMake(server, player, id) {
    var why = this.base(player)
    if (why) return why
    var r = this.recipe(id)
    if (!r) return `no workshop recipe ${id}`
    if (TtlArtifice.rank(player) < Number(r.rank)) return `needs rank ${r.rank} (${TtlArtifice.rankDef(r.rank).title})`
    if (!this.near(player, r.station === 'altar' ? 'altar' : 'bench')) return r.station === 'altar' ? 'made at a Bone Altar' : 'not at a Workshop Bench'
    var short = this.missing(player, r.inputs)
    if (short.length) return `missing ${short.join(', ')}`
    if (r.coins && !TtlEcon.canPay(player, r.coins)) return `needs ${TtlEcon.text(r.coins)}`
    if (r.road) {
      var parts = String(r.road).split('.')
      var road = parts.pop()
      var rw = TtlRoads.check(player, parts.join('.'), road)
      if (rw) return rw
    }
    return ''
  },

  make(server, player, id) {
    var why = this.checkMake(server, player, id)
    if (why) throw why
    var r = this.recipe(id)
    this.take(server, player, r.inputs)
    if (r.coins) TtlEcon.charge(server, player, r.coins, `workshop:${r.id}`)
    TtlCmd.run(server, `give ${player.username} ${r.output} ${Number(r.count)}`)
    if (r.road) {
      var parts = String(r.road).split('.')
      var road = parts.pop()
      TtlRoads.pay(server, player, { id: parts.join('.'), road: road, reason: `make ${r.id}` })
    }
    var s = TtlArtifice.read(player)
    if (s.unlocked.indexOf(String(r.id)) < 0) {
      s.unlocked.push(String(r.id))
      TtlArtifice.write(player, s)
    }
    console.info(`[ttl] artifice: ${player.username} made ${r.count} ${r.output} (${r.id})`)
    player.tell(Text.green(`Workshop: you made ${TtlCommission.pretty(r.output)}.`))
  },

  // ---- the cursed whetstone (dark) -------------------------------------------------------------------------------------

  checkCurse(server, player) {
    var why = this.base(player)
    if (why) return why
    var conf = this.conf().curse || {}
    if (this.count(player, conf.item || 'ttl:cursed_whetstone') < 1) return 'needs a Cursed Whetstone'
    var hand = player.getMainHandItem()
    if (hand.isEmpty() || Number(hand.getMaxStackSize()) > 1) return 'hold a blade or a tool in your main hand'
    if (TtlArtifice.cursed(hand)) return 'that blade is cursed already'
    return TtlRoads.check(player, 'artifice.engrave', 'dark')
  },

  curse(server, player) {
    var why = this.checkCurse(server, player)
    if (why) throw why
    var conf = this.conf().curse || {}
    var hand = player.getMainHandItem()
    if (!TtlArtifice.setTag(hand, TtlArtifice.CURSED, TtlLife.uuid(player))) throw 'the curse did not take (item components unavailable)'
    TtlArtifice.addLore(hand, String(conf.lore || 'Cursed'), 'red')
    TtlCmd.run(server, `clear ${player.username} ${conf.item || 'ttl:cursed_whetstone'} 1`)
    var res = TtlRoads.pay(server, player, { id: 'artifice.engrave', road: 'dark', reason: 'cursed whetstone' })
    console.info(`[ttl] artifice: ${player.username} cursed ${hand.id} (roads ok=${res.ok})`)
    player.tell(Text.red('The whetstone screams on the edge. The blade drinks the ash and wants more.'))
  },

  // ---- schematics: bought (honest) or stolen (dark) -------------------------------------------------------------------

  randomSchematic() {
    var pool = (this.conf().schematics || {}).pool || []
    return String(pool[Math.floor(Math.random() * pool.length)])
  },

  checkBuy(server, player) {
    var why = this.base(player)
    if (why) return why
    var sch = this.conf().schematics || {}
    var bands = sch.buy_band || {}
    var low = Object.keys(bands).filter(f => !(typeof TtlRep !== 'undefined' && TtlRep.atLeast(player, f, String(bands[f]))))
    if (low.length) return `${low.map(f => `${f} must be ${bands[f]}`).join(', ')}`
    if (!TtlEcon.canPay(player, sch.buy_price)) return `needs ${TtlEcon.text(sch.buy_price)}`
    return TtlRoads.check(player, 'artifice.schematic', 'good')
  },

  buy(server, player) {
    var why = this.checkBuy(server, player)
    if (why) throw why
    var sch = this.conf().schematics || {}
    if (!TtlEcon.charge(server, player, sch.buy_price, 'schematic')) throw `needs ${TtlEcon.text(sch.buy_price)}`
    var id = this.randomSchematic()
    TtlCmd.run(server, `give ${player.username} ${id}`)
    TtlRoads.pay(server, player, { id: 'artifice.schematic', road: 'good', reason: 'bought a schematic' })
    console.info(`[ttl] artifice: ${player.username} bought ${id}`)
    player.tell(Text.green(`Workshop: the smithy sells you a ${TtlCommission.pretty(id)}. Read it to learn it.`))
    return id
  },

  isNight(player) {
    var n = (this.conf().steal || {}).night || [13000, 23000]
    var t = Number(player.level.getDayTime()) % 24000
    return t >= Number(n[0]) && t <= Number(n[1])
  },

  nearSmithy(player) {
    var st = this.conf().steal || {}
    if (TtlLife.dimensionOf(player) !== TtlLife.OVERWORLD) return false
    var dx = player.getX() - Number(st.smithy.x)
    var dz = player.getZ() - Number(st.smithy.z)
    return dx * dx + dz * dz <= Number(st.radius) * Number(st.radius)
  },

  checkSteal(server, player) {
    var why = this.base(player)
    if (why) return why
    var st = this.conf().steal || {}
    var uid = TtlLife.uuid(player)
    if (this.channels[uid]) return 'already at work on a lock'
    var last = Number(TtlArtifice.read(player).stole || 0)
    var wait = last + Number(st.cooldown_hours) * 3600000 - Date.now()
    if (wait > 0) return `the smithy is still on guard (${Math.ceil(wait / 3600000)} h)`
    var anywhere = this.flag(player, 'anywhere')
    if (!anywhere && !this.nearSmithy(player)) return 'only inside the Dwargon smithy'
    if (!anywhere && !this.isNight(player)) return 'only at night'
    return TtlRoads.check(player, 'artifice.schematic', 'dark')
  },

  steal(server, player) {
    var why = this.checkSteal(server, player)
    if (why) throw why
    var st = this.conf().steal || {}
    var uid = TtlLife.uuid(player)
    var secs = this.flag(player, 'anywhere') ? 2 : Number(st.channel_seconds)
    var c = { x: player.getX(), y: player.getY(), z: player.getZ(), left: secs }
    this.channels[uid] = c
    var name = String(player.username)
    player.tell(Text.red(`You work at the lock of the schematic chest. Hold still for ${secs} seconds.`))
    var self = this
    var tick = () => server.scheduleInTicks(20, () => {
      var p = server.getPlayerList().getPlayerByName(name)
      if (!p || !self.channels[uid]) {
        delete self.channels[uid]
        return
      }
      var dx = p.getX() - c.x
      var dy = p.getY() - c.y
      var dz = p.getZ() - c.z
      var tol = Number(st.move_tolerance)
      if (dx * dx + dy * dy + dz * dz > tol * tol) {
        delete self.channels[uid]
        p.tell(Text.gray('You moved. The lock snaps shut; nothing was taken.'))
        return
      }
      c.left--
      if (c.left > 0) {
        tick()
        return
      }
      delete self.channels[uid]
      self.stolen(server, p)
    })
    tick()
  },

  stolen(server, player) {
    var s = TtlArtifice.read(player)
    s.stole = Date.now()
    TtlArtifice.write(player, s)
    var id = this.randomSchematic()
    TtlCmd.run(server, `give ${player.username} ${id}`)
    var res = TtlRoads.pay(server, player, { id: 'artifice.schematic', road: 'dark', reason: 'stole a schematic' })
    console.info(`[ttl] artifice: ${player.username} stole ${id} from the Dwargon smithy (roads ok=${res.ok})`)
    player.tell(Text.red(`You slip away with a ${TtlCommission.pretty(id)}. Dwargon will not forget it.`))
  },

  // ---- the Workshop screen -------------------------------------------------------------------------------------------

  menu(server, player) {
    var s = TtlArtifice.read(player)
    var def = TtlArtifice.rankDef(s.rank)
    var next = TtlArtifice.rankDef(s.rank + 1)
    var pts = TtlArtifice.conf().points || {}
    var items = []
    var status = def
      ? [`Rank ${s.rank}: ${def.title}`, `Points: ${s.points}${next ? ` (next: ${next.title} at ${next.points})` : ''}`,
        `This week: ${s.week}/${pts.weekly_cap} (crafting ${s.craft}/${pts.craft_weekly_cap})`, `Golems you may keep: ${def.constructs}`]
      : ['No charter yet.', 'Bring three schematics (learned or carried)', 'to a Workshop Bench and sign the charter.']
    items.push({ slot: 4, item: 'tensura:smithing_bench', name: def ? `Workshop of a ${def.title}` : 'The Workshop', color: '#FFD966', lore: status, command: 'ttl artifice status' })
    if (!def) {
      items.push({ slot: 10, item: 'ttl:artificer_charter', name: 'Sign the charter', color: '#55FF55',
        lore: ['Rank 1, Journeyman.', `You know or carry ${TtlArtifice.schematics(player).length} schematics.`], command: 'ttl artifice charter' })
    } else {
      items.push({ slot: 10, item: 'ttl:artificer_charter', name: 'Your charter', color: '#55FF55',
        lore: [`Signed. ${s.metals ? Object.keys(s.metals).length : 0} metals worked.`], command: 'ttl artifice status' })
    }
    items.push({ slot: 12, item: 'minecraft:writable_book', name: 'Commissions', color: '#55FFFF',
      lore: ['Contracts from Kaijin\'s forge and the Dwargon smithy.', 'Coin, reputation, points, rare schematics.'], command: 'ttl artifice commissions' })
    items.push({ slot: 13, item: 'minecraft:chest', name: 'Deliver commissions', color: '#55FFFF',
      lore: ['Hand in what is ready.'], command: 'ttl artifice commission turnin' })
    items.push({ slot: 14, item: 'ttl:engraving_chisel', name: 'Engrave your work', color: '#C9A0FF',
      lore: ['Rank 2+. Hold an item you made yourself.', 'Tensura\'s engravings, one per item.'], command: 'ttl artifice engrave' })
    items.push({ slot: 16, item: 'minecraft:crafting_table', name: 'Workshop recipes', color: '#C9A0FF',
      lore: ['The chisel, the Warden core and more,', 'unlocked by rank.'], command: 'ttl artifice make' })
    items.push({ slot: 20, item: 'tensura:long_sword_schematic', name: 'Buy a schematic', color: '#FFD966',
      lore: [`${TtlEcon.text((this.conf().schematics || {}).buy_price)}, Dwargon friendly or better.`, 'The honest road.'], command: 'ttl artifice schematic buy' })
    items.push({ slot: 22, item: 'minecraft:book', name: 'How the workshop works', color: '#FFFFFF',
      lore: ['The guide pages of the paths.'], command: 'ttl guide paths' })
    items.push({ slot: 24, item: 'ttl:cursed_whetstone', name: 'The dark road', color: '#AA3333',
      lore: ['A cursed whetstone, made at a Bone Altar', 'from soul ash. Stolen schematics.', 'Faster. Never free.'], command: 'ttl roads' })
    server.runCommandSilent(`ttlmenu ${player.username} ${JSON.stringify({ title: 'Workshop', rows: 3, items: items })}`)
  },

  // Clickable chat line: [label] buttons that run a command as the player.
  buttons(server, player, intro, list) {
    var line = [{ text: `${intro} `, color: 'gold' }]
    list.forEach(b => line.push({ text: `[${b.label}]`, color: b.color || 'aqua', clickEvent: { action: 'run_command', value: b.command },
      hoverEvent: { action: 'show_text', contents: b.hover || b.label } }, ' '))
    server.runCommandSilent(`tellraw ${player.username} ${JSON.stringify(line)}`)
  }
}

// Right-click a Workshop Bench (main hand, not sneaking) opens the Workshop screen in Life 2.
BlockEvents.rightClicked('ttl:workshop_bench', event => {
  var player = event.player
  try {
    if (!player || String(event.hand) !== 'MAIN_HAND' || player.isShiftKeyDown()) return
    var server = player.getServer()
    if (TtlLife.phase(player) !== 'life2') {
      player.tell(Text.gray('The bench is cold. Its craft belongs to souls reborn in the Tensura world.'))
    } else {
      TtlWorkshop.menu(server, player)
    }
  } catch (e) {
    console.error(`[ttl] artifice: workshop bench click failed: ${e}`)
    return
  }
  // event.cancel() exits by throwing (KubeJS EventExit): never inside a try that catches it.
  event.cancel()
})
