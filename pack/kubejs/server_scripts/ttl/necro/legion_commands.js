// priority: 60
// Legion and tomb commands (WP-N2; Brigadier merges them into the /ttl tree). API: necro/legion.js, necro/sanctum.js.
// WP-N3 adds its own literals under /ttl necro (rite, rank, licence, status, expect); this file owns the ones below.
// Players: /ttl necro raise <skeleton|zombie> [dust|ash] [<label>]   raise at your Bone Altar (dust = grey, ash = dark)
//          /ttl necro knight <name> [dust|ash]                      a Death Knight (rank 3+, the gear, 32 dust or ash + a corpse)
//          /ttl necro stow [all|<id>]                               put your dead near you to sleep in the tomb
//          /ttl necro rouse [all|<id>]                              wake sleeping dead at the altar
//          /ttl necro recall                                        your loaded dead within 64 blocks come to you
//          /ttl necro stand <all|<id>> <on|off>                     tomb guards (no AI) or back to life
//          /ttl necro rest                                          lay the dead under a grave marker to rest (the Keeper)
//          /ttl necro muster                                        count your army; a nation at war holds the war cap 24 h
//          /ttl necro sanctum                                       what your tomb is and what it needs to grow
//          /ttl necro legion                                        your legion
// Ops:     /ttl necro legion info <player>                          the record
//          /ttl necro legion altar <player> <pos>                   test: the player keeps the altar at pos (source dimension)
//          /ttl necro legion sanctum <player>                       force a tomb check at the player's nearest own altar
//          /ttl necro legion corpse <killer> <victim> <arena|war|npc>   test: the kill pays ash + corpse (scope and bot rule off)
//          /ttl necro legion pvp <owner> <victim>                   the PvP verdict for the owner's dead against the victim
//          /ttl necro legion sweep                                  run the sweep now
//          /ttl necro legion test <player> <what> [<n>]             test hooks: rank <n> | servercap <n> (-1 = off) |
//                                                                   servercapnow (the cap = the dead awake now) | muster |
//                                                                   reset (discard the soul's dead, wipe its record, ash victims)
//          /ttl necro legion expect <player> <field> <value>        test assertion: prints "ttl: ..." when it does not hold
//            fields: awake, dormant, knights, fallen, entities (loaded, tagged), owner_set (loaded with Tensura's permanent
//                    owner = the player), named (loaded with a Tensura name), army (the last muster), muster (yes|no),
//                    corpses, points (paid), queue (jobs waiting), server_awake, altars, rank, cap, dust, ash (held),
//                    last (the last result code), sanctum (tier at the nearest own altar, a fresh check), sanctum_why,
//                    sanctum_locked, niches, try_raise_dust, try_raise_ash, try_knight_ash, try_knight_dust, try_rest,
//                    try_rouse_fallen (the refusal for the first fallen knight), pvp_<victim> (ok|refused)
const TtlLegionCmd = {
  facts(server, p) {
    var L = TtlLegion
    var uuid = L.uid(p)
    var rec = L.record(server, uuid)
    var out = {}
    var near = L.near(uuid, p, 256)
    out.awake = String(L.awake(rec))
    out.dormant = String(L.dormant(rec))
    out.knights = String(L.knights(rec))
    out.fallen = String(rec.list.filter(x => x.st === 'fallen').length)
    out.entities = String(near.length)
    out.owner_set = String(near.filter(e => L.permanentOwner(e) === uuid).length)
    out.named = String(near.filter(e => L.tname(e) !== '').length)
    out.army = String(rec.army ? rec.army.n : 0)
    out.muster = L.mustered(rec) ? 'yes' : 'no'
    out.corpses = String(L.corpses(rec).length)
    out.points = String(rec.pts || 0)
    out.queue = String(L.queue(server).filter(j => j.o === uuid).length)
    out.server_awake = String(L.serverAwake(server))
    out.altars = String(L.altarsOf(server, uuid).length)
    out.rank = String(L.rank(p))
    out.cap = String(L.cap(p, rec))
    out.dust = String(L.count(server, p, 'ttl:bone_dust'))
    out.ash = String(L.count(server, p, 'ttl:soul_ash'))
    out.last = String(rec.last || 'none')
    return out
  },

  field(server, p, field) {
    var L = TtlLegion
    var f = this.facts(server, p)
    if (field in f) return f[field]
    if (/^sanctum/.test(field) || field === 'niches') {
      var altar = L.nearAltar(server, p) || L.altarsOf(server, L.uid(p))[0]
      if (!altar) return 'noaltar'
      var r = TtlSanctum.check(server, altar.key, p, 'test')
      if (field === 'sanctum') return String(r.tier)
      if (field === 'sanctum_why') return String(r.why)
      if (field === 'sanctum_locked') return String(r.locked || 'none')
      return String(r.niches)
    }
    if (field === 'try_raise_dust' || field === 'try_raise_ash') return L.raiseRefusal(server, p, 'skeleton', field.substring(10), null) || 'ok'
    if (field === 'try_knight_dust' || field === 'try_knight_ash') return L.knightRefusal(server, p, field.substring(11)) || 'ok'
    if (field === 'try_rest') return L.restRefusal(server, p) || 'ok'
    if (field === 'try_rouse_fallen') {
      var rec = L.record(server, L.uid(p))
      var gone = rec.list.filter(x => x.st === 'fallen')[0]
      return gone ? L.rouseRefusal(server, p, gone, L.nearAltar(server, p)) || 'ok' : 'none fallen'
    }
    var m = /^pvp_(.+)$/.exec(field)
    if (m) {
      var v = server.getPlayerList().getPlayerByName(m[1])
      if (!v) throw `${m[1]} is not online`
      return L.pvp(server, p, v).ok ? 'ok' : 'refused'
    }
    throw `unknown field ${field} (one of ${Object.keys(f).join(', ')}, sanctum, sanctum_why, sanctum_locked, niches, try_raise_dust|ash, try_knight_dust|ash, try_rest, try_rouse_fallen, pvp_<victim>)`
  },

  // A refusal the player reads; ok results speak for themselves (legion.js tells them).
  report(player, res) {
    if (!res.ok) TtlLegion.tellWhy(player, res.why)
    return res.ok ? 1 : 0
  },

  reset(server, p) {
    var uuid = TtlLegion.uid(p)
    var tag = `ttl.legion.${uuid}`
    TtlLegion.levels(server).forEach(level => {
      level.getEntities().forEach(e => {
        if (!e.isPlayer() && e.getTags().contains(tag)) e.discard()
      })
    })
    TtlLegion.drop(server, uuid)
    var all = TtlLegion.altars(server)
    Object.keys(all).forEach(k => { if (all[k].o === uuid) TtlLegion.forgetAltar(server, k) })
    TtlLegion.saveQueue(server, TtlLegion.queue(server).filter(j => j.o !== uuid))
    p.persistentData.remove(TtlLegion.VICTIMS)
    p.persistentData.remove(TtlLegion.TESTRANK)
  }
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] legion command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var me = ctx => ctx.source.getPlayerOrException()
  var srv = ctx => ctx.source.getServer()
  var target = (ctx, name) => Arguments.PLAYER.getResult(ctx, name || 'target')
  var str = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var which = (ctx, has) => (has ? str(ctx, 'which') : 'all')

  var raise = (hasRoad, hasLabel) => ctx => {
    var p = me(ctx)
    var label = hasLabel ? String(Arguments.GREEDY_STRING.getResult(ctx, 'label')) : ''
    return TtlLegionCmd.report(p, TtlLegion.raise(srv(ctx), p, str(ctx, 'kind'), hasRoad ? str(ctx, 'road') : 'dust', label))
  }
  var knight = hasRoad => ctx => {
    var p = me(ctx)
    return TtlLegionCmd.report(p, TtlLegion.knight(srv(ctx), p, str(ctx, 'name'), hasRoad ? str(ctx, 'road') : 'dust'))
  }
  var stow = has => ctx => {
    var p = me(ctx)
    return TtlLegionCmd.report(p, TtlLegion.stow(srv(ctx), p, which(ctx, has)))
  }
  var rouse = has => ctx => {
    var p = me(ctx)
    return TtlLegionCmd.report(p, TtlLegion.rouse(srv(ctx), p, which(ctx, has)))
  }
  var recall = ctx => {
    var p = me(ctx)
    var r = TtlLegion.recall(srv(ctx), p)
    if (r.ok) p.tell(Text.darkPurple(`${r.n} of your dead answer the call.`))
    return TtlLegionCmd.report(p, r)
  }
  var stand = ctx => {
    var p = me(ctx)
    var on = str(ctx, 'mode') !== 'off'
    var r = TtlLegion.stand(srv(ctx), p, str(ctx, 'which'), on)
    if (r.ok) p.tell(Text.darkPurple(on ? `${r.n} of your dead stand guard and do not move.` : `${r.n} of your dead move again.`))
    return TtlLegionCmd.report(p, r)
  }
  var rest = ctx => {
    var p = me(ctx)
    return TtlLegionCmd.report(p, TtlLegion.rest(srv(ctx), p))
  }
  var muster = ctx => {
    var p = me(ctx)
    var r = TtlLegion.muster(srv(ctx), p, false)
    if (!r.ok) return TtlLegionCmd.report(p, r)
    p.tell(Text.darkPurple(`Your army: ${r.army} named dead within ${TtlLegion.num(TtlLegion.conf(), 'muster_radius', 32)} blocks.`))
    p.tell(Text.gray(r.war ? `Your nation is at war: your legion may grow to ${TtlLegion.cap(p, TtlLegion.record(srv(ctx), TtlLegion.uid(p)))} awake for ${TtlLegion.num(TtlLegion.conf(), 'muster_hours', 24)} hours.` : 'Only a nation at war (or about to be) holds a war muster; the count is kept.'))
    return 1
  }
  var sanctum = ctx => {
    var p = me(ctx)
    var server = srv(ctx)
    var altar = TtlLegion.nearAltar(server, p)
    if (!altar) {
      var mine = TtlLegion.altarsOf(server, TtlLegion.uid(p))
      if (mine.length === 0) {
        p.tell(Text.gray('You keep no Bone Altar. Craft one (bone blocks, a candle, rotten flesh, cobbled deepslate) and place it.'))
        return 0
      }
      mine.forEach(a => TtlSanctum.lines(TtlSanctum.cached(server, a.key)).forEach(l => p.tell(Text.gray(`${a.x} ${a.y} ${a.z}: ${l}`))))
      p.tell(Text.gray('Stand at one of your altars to check it again.'))
      return 1
    }
    TtlSanctum.lines(TtlSanctum.check(server, altar.key, p, true)).forEach(l => p.tell(Text.darkPurple(l)))
    return 1
  }
  var legion = ctx => {
    var p = me(ctx)
    TtlLegion.lines(srv(ctx), p).forEach(l => p.tell(Text.of(l)))
    return 1
  }

  // ---- ops ----
  var info = ctx => {
    var p = target(ctx)
    var server = srv(ctx)
    var f = TtlLegionCmd.facts(server, p)
    say(ctx, `legion ${p.username}: ${Object.keys(f).sort().map(k => `${k}=${f[k]}`).join(' ')}`)
    TtlLegion.lines(server, p).forEach(l => say(ctx, l))
    return 1
  }
  var altar = ctx => {
    var p = target(ctx)
    var pos = Arguments.BLOCK_POS.getResult(ctx, 'pos')
    var dim = String(ctx.source.getLevel().dimension)
    var why = TtlLegion.claimAltar(srv(ctx), p, dim, pos.getX(), pos.getY(), pos.getZ())
    if (why) throw why
    say(ctx, `legion ${p.username}: keeps the altar at ${TtlLegion.altarKey(dim, pos.getX(), pos.getY(), pos.getZ())}`)
    return 1
  }
  var sanctumOf = ctx => {
    var p = target(ctx)
    var server = srv(ctx)
    var a = TtlLegion.nearAltar(server, p) || TtlLegion.altarsOf(server, TtlLegion.uid(p))[0]
    if (!a) throw `${p.username} keeps no altar`
    var r = TtlSanctum.check(server, a.key, p, 'test')
    say(ctx, `sanctum ${a.key}: tier=${r.tier} why=${r.why} air=${r.air} locked=${r.locked || 'none'} niches=${r.niches} ${r.ms} ms`)
    TtlSanctum.lines(r).forEach(l => say(ctx, l))
    return 1
  }
  var corpse = ctx => {
    var k = target(ctx, 'killer')
    var v = target(ctx, 'victim')
    var why = TtlLegion.onPlayerKill(srv(ctx), k, v, str(ctx, 'how'), true)
    say(ctx, why ? `legion ${k.username}: no corpse of ${v.username} (${why})` : `legion ${k.username}: took the corpse of ${v.username}`)
    return 1
  }
  var pvp = ctx => {
    var o = target(ctx, 'owner')
    var v = target(ctx, 'victim')
    var r = TtlLegion.pvp(srv(ctx), o, v)
    say(ctx, `legion pvp ${o.username} -> ${v.username}: ${r.ok ? 'allowed' : 'refused'} (${r.why})`)
    return 1
  }
  var sweep = ctx => {
    TtlLegion.sweep(srv(ctx))
    say(ctx, `legion: swept (${TtlLegion.serverAwake(srv(ctx))} awake on the server)`)
    return 1
  }
  var test = hasN => ctx => {
    var p = target(ctx)
    var server = srv(ctx)
    var what = str(ctx, 'what')
    var n = hasN ? Number(Arguments.INTEGER.getResult(ctx, 'n')) : 0
    if (what === 'rank') {
      p.persistentData.putInt(TtlLegion.TESTRANK, n)
    } else if (what === 'servercap') {
      if (n < 0) server.persistentData.remove(TtlLegion.TESTCAP)
      else server.persistentData.putInt(TtlLegion.TESTCAP, n)
    } else if (what === 'servercapnow') {
      server.persistentData.putInt(TtlLegion.TESTCAP, TtlLegion.serverAwake(server))
    } else if (what === 'muster') {
      TtlLegion.muster(server, p, true)
    } else if (what === 'reset') {
      TtlLegionCmd.reset(server, p)
    } else {
      throw 'test hooks: rank <n>, servercap <n>, servercapnow, muster, reset'
    }
    say(ctx, `legion ${p.username}: ${what}${hasN ? ` ${n}` : ''}`)
    return 1
  }
  var expect = ctx => {
    var p = target(ctx)
    var field = str(ctx, 'field')
    var want = str(ctx, 'value')
    var got = TtlLegionCmd.field(srv(ctx), p, field)
    if (got !== want) throw `${p.username}: expected ${field}=${want}, got ${got}`
    say(ctx, `legion ${p.username}: ${field}=${want} as expected`)
    return 1
  }

  var op = src => src.hasPermission(2)
  event.register(Commands.literal('ttl')
    .then(Commands.literal('necro')
      .then(Commands.literal('raise')
        .then(Commands.argument('kind', Arguments.STRING.create(event))
          .executes(logged(raise(false, false)))
          .then(Commands.argument('road', Arguments.STRING.create(event))
            .executes(logged(raise(true, false)))
            .then(Commands.argument('label', Arguments.GREEDY_STRING.create(event)).executes(logged(raise(true, true)))))))
      .then(Commands.literal('knight')
        .then(Commands.argument('name', Arguments.STRING.create(event))
          .executes(logged(knight(false)))
          .then(Commands.argument('road', Arguments.STRING.create(event)).executes(logged(knight(true))))))
      .then(Commands.literal('stow')
        .executes(logged(stow(false)))
        .then(Commands.argument('which', Arguments.STRING.create(event)).executes(logged(stow(true)))))
      .then(Commands.literal('rouse')
        .executes(logged(rouse(false)))
        .then(Commands.argument('which', Arguments.STRING.create(event)).executes(logged(rouse(true)))))
      .then(Commands.literal('recall').executes(logged(recall)))
      .then(Commands.literal('stand')
        .then(Commands.argument('which', Arguments.STRING.create(event))
          .then(Commands.argument('mode', Arguments.STRING.create(event)).executes(logged(stand)))))
      .then(Commands.literal('rest').executes(logged(rest)))
      .then(Commands.literal('muster').executes(logged(muster)))
      .then(Commands.literal('sanctum').executes(logged(sanctum)))
      .then(Commands.literal('legion')
        .executes(logged(legion))
        .then(Commands.literal('info').requires(op)
          .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(info))))
        .then(Commands.literal('altar').requires(op)
          .then(Commands.argument('target', Arguments.PLAYER.create(event))
            .then(Commands.argument('pos', Arguments.BLOCK_POS.create(event)).executes(logged(altar)))))
        .then(Commands.literal('sanctum').requires(op)
          .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(sanctumOf))))
        .then(Commands.literal('corpse').requires(op)
          .then(Commands.argument('killer', Arguments.PLAYER.create(event))
            .then(Commands.argument('victim', Arguments.PLAYER.create(event))
              .then(Commands.argument('how', Arguments.STRING.create(event)).executes(logged(corpse))))))
        .then(Commands.literal('pvp').requires(op)
          .then(Commands.argument('owner', Arguments.PLAYER.create(event))
            .then(Commands.argument('victim', Arguments.PLAYER.create(event)).executes(logged(pvp)))))
        .then(Commands.literal('sweep').requires(op).executes(logged(sweep)))
        .then(Commands.literal('test').requires(op)
          .then(Commands.argument('target', Arguments.PLAYER.create(event))
            .then(Commands.argument('what', Arguments.STRING.create(event))
              .executes(logged(test(false)))
              .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(test(true)))))))
        .then(Commands.literal('expect').requires(op)
          .then(Commands.argument('target', Arguments.PLAYER.create(event))
            .then(Commands.argument('field', Arguments.STRING.create(event))
              .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expect)))))))))
})
