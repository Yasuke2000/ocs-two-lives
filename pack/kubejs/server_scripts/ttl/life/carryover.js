// priority: 70
// Soul carryover items (design/master-plan.md §4, design/architecture/sprint3-4.md S1, numbers in
// design/data/carryover.toml). The strip itself (ender chest, Curios, soulbound kept, banned stashed) is
// life/mortal_banned.js (TtlStash); this file adds what a soul gets on top of it:
//   - Soul Gem (ttl:soul_gem, tag ttl:soulbound): issued once on the first Life 1 login, kept through the death by
//     the soulbound tag, re-issued at rebirth with the Life 1 verdict as its lore. Inert in Life 1; in Life 2 a
//     right-click gives a short Regeneration + Resistance echo, once per cooldown.
//   - Remembered Enchantment: death.js calls lifeEnds before the strip and the soul remembers the best enchantment
//     it had on it; corridor_flow.js calls restore at rebirth and a Craft-heavy Hero+ gets it back as a book.
// Persistent data (player): ttl.soul.gem (gem issued once), ttl.soul.book ("<enchantment id>|<level>" remembered at
// death, removed at rebirth), ttl.soul.gemUse (ms timestamp of the last echo). Ops: /ttl soul <player> (see below).
const TtlSoul = {
  GEM: 'ttl:soul_gem',
  FLAG: 'ttl.soul.gem',
  BOOK: 'ttl.soul.book',
  USED: 'ttl.soul.gemUse',
  MARK: 'ttl_remembered',

  conf() {
    return TtlData.carryover
  },

  // Text inside an SNBT single-quoted string.
  esc(text) {
    return String(text).replace(/\\/g, '\\\\').replace(/'/g, "\\'")
  },

  fill(template, vars) {
    return String(template).replace(/\{(\w+)\}/g, (m, k) => (vars[k] === undefined ? m : String(vars[k])))
  },

  // `minecraft:lore=[...]` component value: gray, non-italic lines.
  lore(lines, vars) {
    var parts = lines.map(l => `'${this.esc(JSON.stringify({ text: this.fill(l, vars || {}), color: 'gray', italic: false }))}'`)
    return `[${parts.join(',')}]`
  },

  // Stacks of this body that `pick` accepts, in every place a soul carries things (inventory, ender chest, Curios).
  stacks(player, pick) {
    return TtlStash.places(player).map(p => p.get()).filter(s => !s.isEmpty() && pick(s))
  },

  isGem(stack) {
    return !stack.isEmpty() && String(stack.id) === this.GEM
  },

  gemCount(player) {
    return this.stacks(player, s => this.isGem(s)).length
  },

  components(server, stack) {
    return stack.save(server.registryAccess()).getCompound('components')
  },

  isRemembered(server, stack) {
    return String(stack.id) === 'minecraft:enchanted_book' && this.components(server, stack).getCompound('minecraft:custom_data').contains(this.MARK)
  },

  // The Life 1 verdict as lore variables, or null for a soul without a record.
  verdict(player) {
    var rec = TtlKarma.record(player)
    if (!rec) return null
    var best = null
    Object.keys(rec.axes || {}).forEach(a => {
      if (best === null || rec.axes[a] > rec.axes[best]) best = a
    })
    var tier = TtlKarma.tierOf(player)
    var prefix = rec.dark ? `${TtlData.karma.dark.prefix} ` : ''
    return { title: `${prefix}${tier.title}`, score: rec.score, days: rec.days, axis: best || 'none' }
  },

  giveGem(server, player) {
    var vars = this.verdict(player)
    var lines = vars ? this.conf().gem.lore_judged : this.conf().gem.lore_unjudged
    server.runCommandSilent(`give ${player.username} ${this.GEM}[minecraft:lore=${this.lore(lines, vars)}]`)
    player.persistentData.putBoolean(this.FLAG, true)
  },

  // First Life 1 login: one gem per soul, never a second one.
  issueFirst(server, player) {
    if (player.persistentData.getBoolean(this.FLAG) || this.gemCount(player) > 0) return false
    this.giveGem(server, player)
    console.info(`[ttl] soul: ${player.username} received a Soul Gem`)
    return true
  },

  // The strongest enchantment on this body: {id, level} or null. Highest level wins, the first one found on a tie.
  // Items are read through their serialized form (components minecraft:enchantments / stored_enchantments, 1.21.1:
  // {levels: {id: level}}); curses do not count.
  bestEnchantment(server, player) {
    var best = null
    this.stacks(player, () => true).forEach(stack => {
      var comps = this.components(server, stack)
      ;['minecraft:enchantments', 'minecraft:stored_enchantments'].forEach(key => {
        var box = comps.getCompound(key)
        var levels = box.contains('levels') ? box.getCompound('levels') : box
        var ids = []
        levels.getAllKeys().forEach(k => ids.push(String(k)))
        ids.forEach(id => {
          if (id === 'show_in_tooltip' || /_curse$/.test(id)) return
          var level = Number(levels.getInt(id))
          if (level > 0 && (best === null || level > best.level)) best = { id: id, level: level }
        })
      })
    })
    return best
  },

  // Craft-heavy Hero+: the tier is high enough and the book axis is this soul's strongest, at a minimum score.
  qualifies(player) {
    var rec = TtlKarma.record(player)
    if (!rec) return false
    var cfg = this.conf().book
    if (TtlKarma.tierIndex(rec.tier) < TtlKarma.tierIndex(cfg.min_tier)) return false
    var mine = (rec.axes || {})[cfg.axis] || 0
    if (mine < cfg.min_axis_score) return false
    return Object.keys(rec.axes).every(a => mine >= rec.axes[a])
  },

  giveBook(server, player, memory) {
    var cfg = this.conf().book
    var parts = String(memory).split('|')
    var level = Math.max(1, Math.min(Number(parts[1]) || 1, cfg.max_level))
    var id = parts[0]
    server.runCommandSilent(`give ${player.username} minecraft:enchanted_book[minecraft:stored_enchantments={levels:{"${id}":${level}}},minecraft:custom_data={${this.MARK}:1b},minecraft:lore=${this.lore(cfg.lore)}]`)
    console.info(`[ttl] soul: ${player.username} remembers ${id} ${level}`)
    return `${id} ${level}`
  },

  // Life 1 death, before the strip (death.js): remember the best enchantment while it is still on the body.
  lifeEnds(server, player) {
    var data = player.persistentData
    data.remove(this.BOOK)
    var best = this.bestEnchantment(server, player)
    if (best) data.putString(this.BOOK, `${best.id}|${best.level}`)
    console.info(`[ttl] soul: ${player.username} Life 1 death, best enchantment ${best ? `${best.id} ${best.level}` : 'none'}`)
  },

  // Rebirth, after the inventory clear and TtlStash.restore (corridor_flow.js): the gem is re-issued with the verdict
  // (this also repairs a lost or duplicated one) and a qualifying soul gets its remembered enchantment.
  restore(server, player) {
    var data = player.persistentData
    var name = player.username
    try {
      // The kept gem came back with the soulbound stacks; replace it so every soul holds exactly one, now judged.
      server.runCommandSilent(`quietly clear ${name} ${this.GEM}`)
      this.giveGem(server, player)
    } catch (e) {
      console.error(`[ttl] soul: ${name} gem re-issue failed: ${e}`)
    }
    var memory = String(data.getString(this.BOOK))
    data.remove(this.BOOK)
    try {
      if (memory && this.qualifies(player)) {
        this.giveBook(server, player, memory)
        TtlCorridor.voice(server, name, 'One enchantment of your craft is remembered.')
      }
    } catch (e) {
      console.error(`[ttl] soul: ${name} remembered enchantment failed: ${e}`)
    }
  },

  // `/ttl reset`: a fresh Life 1 owes nothing to an old soul. Also drops the stash and kept soulbound stacks.
  clear(player) {
    var data = player.persistentData
    var keys = [this.FLAG, this.BOOK, this.USED]
    if (typeof TtlStash !== 'undefined') keys.push(TtlStash.BANNED, TtlStash.KEEP, TtlStash.TOLD)
    keys.forEach(k => data.remove(k))
  },

  waitMs(player) {
    return this.conf().gem.life2.cooldown_minutes * 60000 - (Date.now() - (Number(player.persistentData.getString(this.USED)) || 0))
  },

  // The echo (Life 2 right-click). Returns the line to show the player; throws a line for a refusal.
  use(server, player) {
    if (TtlLife.phase(player) !== 'life2') throw 'The gem is dark and silent. It wakes in your second life.'
    var wait = this.waitMs(player)
    if (wait > 0) throw `The gem is still quiet. It answers again in ${Math.ceil(wait / 60000)} min.`
    var tiers = this.conf().gem.life2.tiers
    var echo = tiers[TtlKarma.tierOf(player).id] || tiers.underdog
    var name = player.username
    server.runCommandSilent(`effect give ${name} minecraft:regeneration ${echo.seconds} ${echo.amplifier} true`)
    server.runCommandSilent(`effect give ${name} minecraft:resistance ${echo.seconds} ${echo.amplifier} true`)
    player.persistentData.putString(this.USED, String(Date.now()))
    console.info(`[ttl] soul: ${name} gem echo (${echo.seconds}s, level ${echo.amplifier + 1})`)
    return 'An echo of your first life steadies you.'
  }
}

// One Soul Gem per soul on the first Life 1 login. join.js puts a new player into Life 1 20 ticks after the login, so
// wait until then. Souls who were already playing when this shipped get theirs on their next login.
PlayerEvents.loggedIn(event => {
  var player = event.player
  var server = event.server
  server.scheduleInTicks(60, () => {
    try {
      if (TtlLife.phase(player) === 'life1') TtlSoul.issueFirst(server, player)
    } catch (e) {
      console.error(`[ttl] soul: first gem for ${player.username} failed: ${e}`)
    }
  })
})

// Soulbound items never leave a Life 1 body (the toss is cancelled and the item goes back to the inventory).
ItemEvents.dropped(event => {
  var player = event.player
  try {
    if (!player || TtlLife.phase(player) !== 'life1' || !TtlStash.isSoulbound(event.item)) return
    player.tell(Text.gold('Your soul will not let this go.'))
  } catch (e) {
    console.error(`[ttl] soul: drop check failed: ${e}`)
    return
  }
  // event.cancel() exits by throwing (KubeJS EventExit): never inside a try that catches it.
  event.cancel()
})

ItemEvents.rightClicked(event => {
  var player = event.player
  try {
    if (!player || !TtlSoul.isGem(event.item)) return
    player.tell(Text.gold(TtlSoul.use(player.getServer(), player)))
  } catch (e) {
    if (player) player.tell(Text.of(String(e)))
  }
})

// Ops: /ttl soul <player>                                   what the soul holds
//      /ttl soul <player> give                              issue a Soul Gem if the body holds none
//      /ttl soul <player> use                               test hook: the Life 2 echo, as a right-click would
//      /ttl soul <player> clear                             forget the gem flag, the remembered enchantment and the cooldown
//      /ttl soul expect <player> <field> <value>            test assertion, prints "ttl: ..." when wrong; value is a
//                                                           number, empty/no (= 0) or yes (= at least 1)
//        fields: gem (Soul Gems on the body), book (remembered-enchantment books on the body), ender (ender chest
//                stacks), curios (Curios stacks), memory (an enchantment is remembered from the death), flag (the
//                gem was issued), cooling (the echo is on cooldown)
//      /ttl soul expect <player> has <item> <value>         stacks of an item on the body (full id, or just the
//                                                           path: diamond, soul_gem), same values
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] soul command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var server = ctx => ctx.source.getServer()
  var arg = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))

  var facts = (srv, player) => ({
    gem: TtlSoul.gemCount(player),
    book: TtlSoul.stacks(player, s => TtlSoul.isRemembered(srv, s)).length,
    ender: TtlStash.find(player, () => true, 'ender').length,
    curios: TtlStash.find(player, () => true, 'curios').length,
    memory: String(player.persistentData.getString(TtlSoul.BOOK)) ? 1 : 0,
    flag: player.persistentData.getBoolean(TtlSoul.FLAG) ? 1 : 0,
    cooling: TtlSoul.waitMs(player) > 0 ? 1 : 0
  })
  var describe = f => Object.keys(f).map(k => `${k}=${f[k]}`).join(' ')

  var check = (p, label, got, value) => {
    var ok = value === 'yes' ? got > 0 : (value === 'no' || value === 'empty' || value === 'none') ? got === 0 : got === Number(value)
    if (!ok) throw `${p.username}: expected ${label}=${value}, got ${got}`
  }

  var show = ctx => {
    var p = target(ctx)
    var memory = String(p.persistentData.getString(TtlSoul.BOOK))
    say(ctx, `soul ${p.username}: ${describe(facts(server(ctx), p))}${memory ? ` remembers ${memory}` : ''}`)
    return 1
  }

  var give = ctx => {
    var p = target(ctx)
    if (TtlSoul.gemCount(p) > 0) {
      say(ctx, `soul ${p.username}: already holds a Soul Gem`)
      return 1
    }
    TtlSoul.giveGem(server(ctx), p)
    say(ctx, `soul ${p.username}: Soul Gem issued`)
    return 1
  }

  var use = ctx => {
    var p = target(ctx)
    say(ctx, `soul ${p.username}: ${TtlSoul.use(server(ctx), p)}`)
    return 1
  }

  var clear = ctx => {
    var p = target(ctx)
    ;[TtlSoul.FLAG, TtlSoul.BOOK, TtlSoul.USED].forEach(k => p.persistentData.remove(k))
    say(ctx, `soul ${p.username}: cleared`)
    return 1
  }

  var expect = ctx => {
    var p = target(ctx)
    var field = arg(ctx, 'field')
    var f = facts(server(ctx), p)
    if (!(field in f)) throw `unknown field ${field} (one of ${Object.keys(f).join(', ')}, or has <item>)`
    check(p, field, f[field], arg(ctx, 'value'))
    say(ctx, `soul ${p.username}: ${field}=${arg(ctx, 'value')} as expected`)
    return 1
  }

  var has = ctx => {
    var p = target(ctx)
    var item = arg(ctx, 'item')
    var n = TtlSoul.stacks(p, s => String(s.id) === item || String(s.id).replace(/^.*:/, '') === item).length
    check(p, `has ${item}`, n, arg(ctx, 'value'))
    say(ctx, `soul ${p.username}: has ${item}=${arg(ctx, 'value')} as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('soul')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('expect')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.literal('has')
            .then(Commands.argument('item', Arguments.STRING.create(event))
              .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(has)))))
          .then(Commands.argument('field', Arguments.STRING.create(event))
            .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expect))))))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .executes(logged(show))
        .then(Commands.literal('give').executes(logged(give)))
        .then(Commands.literal('use').executes(logged(use)))
        .then(Commands.literal('clear').executes(logged(clear))))))
})
