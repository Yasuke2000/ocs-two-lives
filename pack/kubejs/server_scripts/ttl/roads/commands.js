// priority: 60
// Two roads commands (Brigadier merges these into the /ttl tree from commands.js). API: roads/roads.js.
// Players: /ttl paths                                    the paths you can walk (guide pages `paths` + a short list in chat)
//          /ttl roads                                    the roads you took (counts per choice; never the karma numbers)
// Ops:     /ttl roads list                               every choice and its routes
//          /ttl roads info <player>                      counts, firsts, today's balance notes, ledger, last result
//          /ttl roads pay <player> <system> <act> <road> [<faction>]   take a route and pay its costs (faction: the victim)
//          /ttl roads witnesses <player>                 who would witness an act where the player stands (R14)
//          /ttl roads log [<n>]                          the newest n (default 10) routes taken
//          /ttl roads items                              test: every path item and block is registered ("ttl: ..." if not)
//          /ttl roads items <player>                     test: the player holds one of every path item and block
//          /ttl roads block <pos> <id>                   test: the block at pos (in the source's dimension) is id
//          /ttl roads test <player> life2|life1|reset    test hooks: Life 2 / Life 1 stage only, forget roads state + ledger
//          /ttl roads expect <player> <field> <value>    test assertion: prints "ttl: ..." when it does not hold
//            fields: chaos2, order2, craft2, faith2 (ledger), carry_<axis> (what the next judgement adds),
//                    count_<id>.<road> (times taken), first_<id>.<road> (yes|no: the first-time line is spent),
//                    try_<id>.<road> (ok or the reason it is refused, e.g. life2only), tide_dark, tide_light (notes today),
//                    last_ok, last_road, last_renown, last_witnesses, last_noted, last_first, last_rep_<faction>
const TtlRoadsCmd = {
  // Every path item and block of WP-N0 (startup_scripts/ttl/items.js, blocks.js; item tag ttl:paths).
  ITEMS: ['soul_ash', 'bone_dust', 'soul_remnant', 'hipokute_salve', 'engraving_chisel', 'cursed_whetstone', 'warden_core',
    'artificer_charter', 'exorcist_licence'],
  BLOCKS: ['bone_altar', 'workshop_bench', 'grave_lantern', 'grave_marker', 'offering_bowl', 'cracked_dam', 'rubble',
    'dragon_egg_cradle'],

  all() {
    return this.ITEMS.concat(this.BLOCKS).map(id => `ttl:${id}`)
  },

  facts(server, player) {
    var s = TtlRoads.read(player)
    var led = TtlRoads.ledger(player)
    var carry = TtlRoads.carry(player) || {}
    var out = {}
    Object.keys(led).forEach(a => {
      out[`${a}2`] = String(led[a])
      out[`carry_${a}`] = String(Math.round(Number(carry[a] || 0) * 10) / 10)
    })
    Object.keys(s.counts).forEach(k => { out[`count_${k}`] = String(s.counts[k]) })
    Object.keys(s.firsts).forEach(k => { out[`first_${k}`] = 'yes' })
    var day = Math.floor(Date.now() / TtlRoads.DAY_MS)
    out.tide_dark = String(s.tide.day === day ? s.tide.dark : 0)
    out.tide_light = String(s.tide.day === day ? s.tide.light : 0)
    var last = s.last || {}
    out.last_ok = last.ok ? 'yes' : 'no'
    out.last_road = String(last.road || 'none')
    out.last_renown = String(last.renown || 0)
    out.last_witnesses = String(last.witnesses || 0)
    out.last_noted = String(last.noted || 0)
    out.last_first = last.first ? 'yes' : 'no'
    Object.keys(last.rep || {}).forEach(f => { out[`last_rep_${f}`] = String(last.rep[f]) })
    return out
  },

  // A field that is not stored has a default instead of "unknown" (count 0, first no, try computed).
  field(server, player, field) {
    var f = this.facts(server, player)
    if (field in f) return f[field]
    var m = /^(count|first|try)_(.+)\.(good|grey|dark)$/.exec(field)
    if (m && m[1] === 'count') return '0'
    if (m && m[1] === 'first') return 'no'
    if (m && m[1] === 'try') return TtlRoads.check(player, m[2], m[3]) || 'ok'
    if (/^last_rep_/.test(field)) return 'none'
    throw `unknown field ${field} (one of ${Object.keys(f).join(', ')}, count_/first_/try_<id>.<road>, last_rep_<faction>)`
  },

  // Players: what each path is and where it starts (discoverability rule of 18/11/2026). Mirrors guide.toml [[paths]].
  pathLines() {
    return [
      'Paths are open to every reborn soul, whatever its Oath or race. Each has a slow good road and a fast dark one.',
      '- Necromancer: raise and keep an undead legion at a Bone Altar; build your own tomb around it.',
      '- Artificer: sign the charter at a Workshop Bench, stamp what you forge and fill the daily commissions to rise four ranks; engrave with a chisel, or take the fast dark road (cursed whetstone, stolen schematics). /ttl artifice',
      '- Crossroads of conscience: hard choices the world puts in your path in the wilds. /ttl choice when you meet one.',
      'Read more: /ttl guide paths   Your roads so far: /ttl roads'
    ]
  }
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] roads command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var str = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))

  var paths = ctx => {
    var player = ctx.source.getPlayerOrException()
    TtlRoadsCmd.pathLines().forEach(l => player.tell(Text.gold(l)))
    if (typeof TtlGuide !== 'undefined') TtlGuide.show(ctx.source.getServer(), player, 'paths', '')
    return 1
  }

  var mine = ctx => {
    var player = ctx.source.getPlayerOrException()
    var lines = TtlRoads.lines(player)
    if (lines.length === 1) player.tell(Text.gray('You have not taken a road yet. See /ttl paths.'))
    lines.forEach(l => player.tell(Text.of(l)))
    return 1
  }

  var list = ctx => {
    TtlRoads.ids().forEach(id => {
      var c = TtlRoads.choice(id)
      say(ctx, `${id} (${c.label}): ${TtlRoads.ROUTES.filter(r => c[r]).map(r => `${r}${r === c.fair ? '*' : ''} ${JSON.stringify(c[r])}`).join(' | ')}`)
    })
    return 1
  }

  var info = ctx => {
    var p = target(ctx)
    var f = TtlRoadsCmd.facts(ctx.source.getServer(), p)
    say(ctx, `roads ${p.username}: ${Object.keys(f).sort().map(k => `${k}=${f[k]}`).join(' ')}`)
    return 1
  }

  var pay = withFaction => ctx => {
    var server = ctx.source.getServer()
    var p = target(ctx)
    var opts = { system: str(ctx, 'system'), act: str(ctx, 'act'), road: str(ctx, 'road'), reason: 'command' }
    if (withFaction) opts.faction = str(ctx, 'faction')
    var res = TtlRoads.pay(server, p, opts)
    if (!res.ok) throw `${p.username} cannot take ${res.id} ${res.road}: ${res.why}`
    say(ctx, `roads ${p.username}: ${res.id} ${res.road} karma=${JSON.stringify(res.karma)} balance=${res.balance}x${res.noted}${res.chronicle ? '' : ' (no chronicle)'} rep=${JSON.stringify(res.rep)} renown=${res.renown} witnesses=${res.witnesses}${res.first ? ' first' : ''}${res.story ? ` story="${res.story}"` : ''}`)
    return 1
  }

  var witnesses = ctx => {
    var p = target(ctx)
    var w = TtlRoads.witnesses(ctx.source.getServer(), p)
    say(ctx, `roads ${p.username}: ${w.total} witnesses (players: ${w.players.join(', ') || 'none'}; NPCs: ${w.npcs})`)
    return 1
  }

  var log = n => ctx => {
    var count = n ? Number(Arguments.INTEGER.getResult(ctx, 'n')) : 10
    var ring = TtlRoads.log(ctx.source.getServer())
    var rows = ring.slice(Math.max(0, ring.length - count))
    if (rows.length === 0) say(ctx, 'roads log: empty')
    rows.forEach(r => say(ctx, `${new Date(r.t).toISOString()} ${r.p} ${r.id} ${r.road} (${r.w} witnesses)`))
    return 1
  }

  var itemsRegistered = ctx => {
    var missing = TtlRoadsCmd.all().filter(id => Item.of(id).isEmpty())
    if (missing.length > 0) throw `not registered: ${missing.join(', ')}`
    say(ctx, `roads: all ${TtlRoadsCmd.all().length} path items and blocks are registered`)
    return 1
  }

  var itemsHeld = ctx => {
    var p = target(ctx)
    var inv = p.getInventory()
    var held = {}
    for (var i = 0; i < inv.getContainerSize(); i++) {
      var s = inv.getItem(i)
      if (!s.isEmpty()) held[String(s.id)] = true
    }
    var missing = TtlRoadsCmd.all().filter(id => !held[id])
    if (missing.length > 0) throw `${p.username} does not hold: ${missing.join(', ')}`
    say(ctx, `roads ${p.username}: holds all ${TtlRoadsCmd.all().length} path items and blocks`)
    return 1
  }

  var block = ctx => {
    var pos = Arguments.BLOCK_POS.getResult(ctx, 'pos')
    var want = String(Arguments.RESOURCE_LOCATION.getResult(ctx, 'id'))
    var got = String(ctx.source.getLevel().getBlock(pos).id)
    if (got !== want) throw `block at ${pos.getX()} ${pos.getY()} ${pos.getZ()} is ${got}, expected ${want}`
    say(ctx, `roads: ${want} at ${pos.getX()} ${pos.getY()} ${pos.getZ()} as expected`)
    return 1
  }

  var test = ctx => {
    var p = target(ctx)
    var what = str(ctx, 'what')
    if (what === 'life2') {
      p.stages.remove('ttl.life1')
      p.stages.remove('ttl.corridor')
      p.stages.add('ttl.life2')
    } else if (what === 'life1') {
      p.stages.remove('ttl.life2')
      p.stages.remove('ttl.corridor')
      p.stages.add('ttl.life1')
    } else if (what === 'reset') {
      TtlRoads.clear(p)
    } else {
      throw 'test hooks: life2, life1, reset'
    }
    say(ctx, `roads ${p.username}: ${what}`)
    return 1
  }

  var expect = ctx => {
    var p = target(ctx)
    var field = str(ctx, 'field')
    var want = str(ctx, 'value')
    var got = TtlRoadsCmd.field(ctx.source.getServer(), p, field)
    if (got !== want) throw `${p.username}: expected ${field}=${want}, got ${got}`
    say(ctx, `roads ${p.username}: ${field}=${want} as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('paths').executes(logged(paths)))
    .then(Commands.literal('roads')
      .executes(logged(mine))
      .then(Commands.literal('list').requires(src => src.hasPermission(2)).executes(logged(list)))
      .then(Commands.literal('log').requires(src => src.hasPermission(2))
        .executes(logged(log(false)))
        .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(log(true)))))
      .then(Commands.literal('info').requires(src => src.hasPermission(2))
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(info))))
      .then(Commands.literal('witnesses').requires(src => src.hasPermission(2))
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(witnesses))))
      .then(Commands.literal('pay').requires(src => src.hasPermission(2))
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('system', Arguments.STRING.create(event))
            .then(Commands.argument('act', Arguments.STRING.create(event))
              .then(Commands.argument('road', Arguments.STRING.create(event))
                .executes(logged(pay(false)))
                .then(Commands.argument('faction', Arguments.STRING.create(event)).executes(logged(pay(true)))))))))
      .then(Commands.literal('items').requires(src => src.hasPermission(2))
        .executes(logged(itemsRegistered))
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(itemsHeld))))
      .then(Commands.literal('block').requires(src => src.hasPermission(2))
        .then(Commands.argument('pos', Arguments.BLOCK_POS.create(event))
          .then(Commands.argument('id', Arguments.RESOURCE_LOCATION.create(event)).executes(logged(block)))))
      .then(Commands.literal('test').requires(src => src.hasPermission(2))
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('what', Arguments.STRING.create(event)).executes(logged(test)))))
      .then(Commands.literal('expect').requires(src => src.hasPermission(2))
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('field', Arguments.STRING.create(event))
            .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expect))))))))
})
