// Two Lives carryover (design/master-plan.md §4, D3):
//   1. At the Life 1 death everything on the body is stripped: inventory (death.js `/clear`), ENDER CHEST and CURIOS
//      slots (this file). Items tagged `ttl:soulbound` are the exception: they wait in persistentData `ttl.soul.keep`
//      and come back at rebirth (corridor_flow.js `rebirth()` calls TtlStash.restore).
//   2. In the Mortal dimensions a Life 1 soul may not hold banned items (design/data/mortal_banned.toml, default: all
//      Tensura mods). Use, placement, pickup and crafting are refused; whatever still gets onto the body is moved into
//      the "soul stash" (persistentData `ttl.stash`) within 2 seconds, and returned at rebirth.
// Both stores are compounds of serialized item stacks (ItemStack#save), key s0, s1, ...
//   3. Iron's Spells casts of the schools in mortal_banned.toml `spell_schools` (blood, eldritch: O-N1) are refused in the
//      Mortal dimensions: Iron's posts the cancellable io.redspace.ironsspellbooks.api.events.SpellPreCastEvent on the
//      server before every player cast (AbstractSpell.attemptInitiateCast, read from the 3.16.3 jar), reached here through
//      NativeEvents.onEvent like Tombstone's CaptureSoulEvent (compat/tombstone_bosses.js). If it cannot be registered
//      the log says so and the fallback is `irons_spellbooks` in `namespaces`.
const TtlStash = {
  BANNED: 'ttl.stash',
  KEEP: 'ttl.soul.keep',
  TOLD: 'ttl.stash.told',
  // Test hook (`/ttl stash <p> soulbound <item>`): ids treated as soulbound until the next script reload.
  extraSoulbound: [],
  emptyStack: null,
  lookup: null,
  curiosWarned: false,
  // True once the SpellPreCastEvent veto is registered (bottom of this file).
  spellVeto: false,
  spellToldAt: {},

  empty() {
    if (!this.emptyStack) this.emptyStack = Java.loadClass('net.minecraft.world.item.ItemStack').EMPTY
    return this.emptyStack
  },

  rules() {
    if (this.lookup) return this.lookup
    var data = TtlData.mortal_banned || {}
    var set = list => {
      var out = {}
      ;(list || []).forEach(v => { out[String(v)] = true })
      return out
    }
    this.lookup = {
      namespaces: set(data.namespaces),
      items: set(data.items),
      allow: set(data.allow),
      tags: (data.tags || []).map(t => String(t)),
      schools: set(data.spell_schools)
    }
    return this.lookup
  },

  isBannedId(id) {
    var r = this.rules()
    if (r.allow[id]) return false
    return !!(r.items[id] || r.namespaces[id.split(':')[0]])
  },

  isBanned(stack) {
    if (stack.isEmpty()) return false
    var id = String(stack.id)
    if (this.isBannedId(id)) return true
    if (this.rules().allow[id]) return false
    var tags = this.rules().tags
    for (var i = 0; i < tags.length; i++) {
      if (stack.hasTag(tags[i])) return true
    }
    return false
  },

  isSoulbound(stack) {
    if (stack.isEmpty()) return false
    return this.extraSoulbound.indexOf(String(stack.id)) >= 0 || !!stack.hasTag('ttl:soulbound')
  },

  // True when a cast of this Iron's school (an id like irons_spellbooks:blood) is refused in this dimension. Any soul in a
  // Mortal dimension: only Life 1 souls are there (life/confine.js), and the rule is about the place.
  spellRefused(dimension, school) {
    return TtlLife.isMortal(String(dimension)) && !!this.rules().schools[String(school)]
  },

  onSpellPreCast(event) {
    var refuse = false
    var player = null
    var school = ''
    try {
      player = event.getEntity()
      school = String(event.getSchoolType().getId())
      refuse = !!player && this.spellRefused(TtlLife.dimensionOf(player), school)
    } catch (e) {
      console.error(`[ttl] stash: spell veto check failed, the cast goes ahead: ${e}`)
      return
    }
    if (!refuse) return
    event.setCanceled(true)
    try {
      var name = String(player.username)
      var now = Date.now()
      if (!this.spellToldAt[name] || now - this.spellToldAt[name] > 60000) {
        this.spellToldAt[name] = now
        player.displayClientMessage(Text.gray('This magic does not answer in a mortal world.'), true)
      }
      console.info(`[ttl] stash: ${name} cast ${String(event.getSpellId())} (${school}) refused in ${TtlLife.dimensionOf(player)}`)
    } catch (e) {
      // the cast is refused either way
    }
  },

  inMortalLife1(player) {
    return TtlLife.phase(player) === 'life1' && TtlLife.isMortal(TtlLife.dimensionOf(player))
  },

  slotOfContainer(container, index, where) {
    return { where: where, get: () => container.getItem(index), set: s => container.setItem(index, s) }
  },

  slotOfHandler(handler, index, where) {
    return { where: where, get: () => handler.getStackInSlot(index), set: s => handler.setStackInSlot(index, s) }
  },

  // Everything on a body that survives a plain /clear: inventory (hotbar, armor, offhand), ender chest, Curios.
  places(player) {
    var out = []
    var inv = player.getInventory()
    for (var i = 0; i < inv.getContainerSize(); i++) out.push(this.slotOfContainer(inv, i, 'inventory'))
    var ender = player.getEnderChestInventory()
    for (var j = 0; j < ender.getContainerSize(); j++) out.push(this.slotOfContainer(ender, j, 'ender'))
    try {
      var api = Java.loadClass('top.theillusivec4.curios.api.CuriosApi')
      var curios = api.getCuriosInventory(player).orElse(null)
      if (curios) {
        curios.getCurios().values().forEach(handler => {
          ;[handler.getStacks(), handler.getCosmeticStacks()].forEach(stacks => {
            for (var k = 0; k < stacks.getSlots(); k++) out.push(this.slotOfHandler(stacks, k, 'curios'))
          })
        })
      }
    } catch (e) {
      if (!this.curiosWarned) console.warn(`[ttl] stash: Curios slots unreadable, skipped: ${e}`)
      this.curiosWarned = true
    }
    return out
  },

  count(player, key) {
    return Number(player.persistentData.getCompound(key).size())
  },

  put(server, player, key, stack) {
    var data = player.persistentData
    var box = data.getCompound(key)
    box.put(`s${box.size()}`, stack.save(server.registryAccess()))
    data.put(key, box)
  },

  // Slots on the body whose stack `pick` accepts; `where` limits them to one place.
  find(player, pick, where) {
    return this.places(player).filter(p => (!where || p.where === where) && !p.get().isEmpty() && pick(p.get()))
  },

  // Moves every matching stack off the body into the store `key`. Returns how many stacks moved.
  stash(server, player, key, pick) {
    var moved = this.find(player, pick)
    var empty = this.empty()
    moved.forEach(p => {
      this.put(server, player, key, p.get())
      p.set(empty)
    })
    return moved.length
  },

  // Gives back every stack in the store `key` and empties it. Returns how many stacks came back.
  give(server, player, key) {
    var data = player.persistentData
    var box = data.getCompound(key)
    var keys = []
    box.getAllKeys().forEach(k => keys.push(String(k)))
    var itemStack = Java.loadClass('net.minecraft.world.item.ItemStack')
    var given = 0
    keys.forEach(k => {
      var stack = itemStack.parseOptional(server.registryAccess(), box.getCompound(k))
      if (stack.isEmpty()) {
        console.error(`[ttl] stash: ${player.username} ${key}.${k} could not be read back, dropped`)
        return
      }
      player.give(stack)
      given++
    })
    data.remove(key)
    return given
  },

  // Life 1 death, before death.js clears the inventory: soulbound stacks are kept for Life 2, banned ones go to the
  // soul stash, then the ender chest and the Curios slots are emptied (the inventory is left to `/clear`).
  lifeEnds(server, player) {
    var data = player.persistentData
    data.remove(this.KEEP)
    var keep = 0
    var stashed = 0
    this.places(player).forEach(p => {
      var s = p.get()
      if (s.isEmpty()) return
      if (this.isSoulbound(s)) {
        this.put(server, player, this.KEEP, s)
        keep++
      } else if (this.isBanned(s)) {
        this.put(server, player, this.BANNED, s)
        stashed++
      }
    })
    var empty = this.empty()
    this.places(player).forEach(p => {
      if (p.where !== 'inventory') p.set(empty)
    })
    // Whatever a mod's slot refused to give up goes through the commands.
    var left = this.places(player).filter(p => p.where !== 'inventory' && !p.get().isEmpty()).length
    if (left > 0) {
      console.warn(`[ttl] stash: ${player.username} still has ${left} ender/Curios stacks, clearing by command`)
      var name = player.username
      for (var n = 0; n < 27; n++) server.runCommandSilent(`quietly item replace entity ${name} enderchest.${n} with minecraft:air`)
      server.runCommandSilent(`quietly curios clear ${name}`)
    }
    console.info(`[ttl] ${player.username} Life 1 strip: ${keep} soulbound kept, ${stashed} banned stashed, ender chest and Curios emptied`)
  },

  // Rebirth, after the inventory clear: soulbound stacks and the soul stash return with the new body.
  restore(server, player) {
    var kept = this.give(server, player, this.KEEP)
    var stashed = this.give(server, player, this.BANNED)
    player.persistentData.remove(this.TOLD)
    if (kept + stashed > 0) {
      TtlCorridor.voice(server, player.username, 'What your soul kept through the passage returns to your hands.')
      console.info(`[ttl] ${player.username} rebirth: ${kept} soulbound and ${stashed} stashed stacks returned`)
    }
  },

  sweep(server, player) {
    var moved = this.stash(server, player, this.BANNED, s => this.isBanned(s))
    if (moved === 0) return 0
    console.info(`[ttl] stash: ${player.username} (life 1) had ${moved} banned stacks, moved to the soul stash`)
    if (!player.persistentData.getBoolean(this.TOLD)) {
      player.persistentData.putBoolean(this.TOLD, true)
      TtlCorridor.voice(server, player.username, 'A weight from another world does not belong in this life. It will wait for you in the next.')
    }
    return moved
  },

  // Refuses an action of a Life 1 soul in the Mortal dimensions; true when the event was cancelled.
  refuse(event, player, stack) {
    try {
      if (!player || !this.inMortalLife1(player) || !this.isBanned(stack)) return false
    } catch (e) {
      console.error(`[ttl] stash: refuse check failed: ${e}`)
      return false
    }
    event.cancel()
    return true
  }
}

ItemEvents.rightClicked(event => {
  TtlStash.refuse(event, event.player, event.item)
})

// Right-clicking a block with a banned item in hand (placing it, using it on the block).
BlockEvents.rightClicked(event => {
  TtlStash.refuse(event, event.player, event.item)
})

ItemEvents.canPickUp(event => {
  TtlStash.refuse(event, event.player, event.item)
})

// A banned block placed by other means (the item check above catches the normal way).
BlockEvents.placed(event => {
  var entity = event.entity
  try {
    if (!entity || String(entity.type) !== 'minecraft:player' || !TtlStash.inMortalLife1(entity) || !TtlStash.isBannedId(String(event.block.id))) return
  } catch (e) {
    console.error(`[ttl] stash: placed check failed: ${e}`)
    return
  }
  event.cancel()
})

// The craft cannot be cancelled from here (ItemEvents.crafted has no result): the sweep moves the output into the
// soul stash on the next tick, the ingredients are spent.
ItemEvents.crafted(event => {
  var player = event.player
  try {
    var server = player.getServer()
    if (!player || !TtlStash.inMortalLife1(player) || !TtlStash.isBanned(event.item)) return
    server.scheduleInTicks(1, () => TtlStash.sweep(server, player))
  } catch (e) {
    console.error(`[ttl] stash: craft check failed: ${e}`)
  }
})

// Safety net for every other way a banned item gets onto a Life 1 body (commands, loot, trades, other mods).
ServerEvents.loaded(event => {
  var server = event.server
  var loop = () => server.scheduleInTicks(40, () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        if (TtlStash.inMortalLife1(p)) TtlStash.sweep(server, p)
      } catch (e) {
        console.error(`[ttl] stash sweep failed for ${p.username}: ${e}`)
      }
    })
    loop()
  })
  loop()
})

// Ops: /ttl stash <player>                          what the soul holds
//      /ttl stash <player> expect <field> <n>       test assertion, prints "ttl: ..." when wrong
//        fields: stash (stacks in the soul stash), kept (soulbound stacks waiting for rebirth), ender (stacks in the
//                ender chest), curios (stacks in Curios slots), banned (banned stacks on the body), soul (soulbound
//                stacks on the body)
//      /ttl stash <player> sweep                    run the banned-item sweep now (Life 1 in the Mortal dimensions)
//      /ttl stash <player> equip <item>             test hook: put one item into the first free Curios slot
//      /ttl stash <player> soulbound <item>         test hook: treat that item id as soulbound until the next reload
//      /ttl stash <player> clear                    empty the soul stash and the kept list (a /ttl reset leaves them)
//      /ttl stash <player> spell <school> <yes|no>  test assertion: is a cast of that Iron's school refused where the player
//                                                   stands; also fails when the SpellPreCastEvent veto is not registered
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] stash command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')

  var facts = player => ({
    stash: TtlStash.count(player, TtlStash.BANNED),
    kept: TtlStash.count(player, TtlStash.KEEP),
    ender: TtlStash.find(player, () => true, 'ender').length,
    curios: TtlStash.find(player, () => true, 'curios').length,
    banned: TtlStash.find(player, s => TtlStash.isBanned(s)).length,
    soul: TtlStash.find(player, s => TtlStash.isSoulbound(s)).length
  })

  var show = ctx => {
    var p = target(ctx)
    var f = facts(p)
    say(ctx, `stash ${p.username}: ${Object.keys(f).map(k => `${k}=${f[k]}`).join(' ')}`)
    return 1
  }

  var expect = ctx => {
    var p = target(ctx)
    var field = String(Arguments.STRING.getResult(ctx, 'field'))
    var want = Number(Arguments.INTEGER.getResult(ctx, 'n'))
    var f = facts(p)
    if (!(field in f)) throw `unknown field ${field} (one of ${Object.keys(f).join(', ')})`
    if (f[field] !== want) throw `${p.username}: expected ${field}=${want}, got ${f[field]} (${Object.keys(f).map(k => `${k}=${f[k]}`).join(' ')})`
    say(ctx, `stash ${p.username}: ${field}=${want} as expected`)
    return 1
  }

  var sweep = ctx => {
    var p = target(ctx)
    if (!TtlStash.inMortalLife1(p)) throw `${p.username} is not a Life 1 soul in the Mortal dimensions`
    say(ctx, `stash ${p.username}: ${TtlStash.sweep(ctx.source.getServer(), p)} stacks moved`)
    return 1
  }

  var equip = ctx => {
    var p = target(ctx)
    var stack = Item.of(String(Arguments.RESOURCE_LOCATION.getResult(ctx, 'item')))
    if (stack.isEmpty()) throw 'unknown item'
    var free = TtlStash.places(p).filter(s => s.where === 'curios' && s.get().isEmpty())
    if (free.length === 0) throw `${p.username} has no free Curios slot`
    free[0].set(stack)
    say(ctx, `stash ${p.username}: ${String(stack.id)} equipped in a Curios slot`)
    return 1
  }

  var soulbound = ctx => {
    var id = String(Arguments.RESOURCE_LOCATION.getResult(ctx, 'item'))
    if (TtlStash.extraSoulbound.indexOf(id) < 0) TtlStash.extraSoulbound.push(id)
    say(ctx, `stash: ${id} counts as soulbound until the next reload`)
    return 1
  }

  var spell = ctx => {
    var p = target(ctx)
    var school = String(Arguments.RESOURCE_LOCATION.getResult(ctx, 'school'))
    var want = String(Arguments.STRING.getResult(ctx, 'refused')) === 'yes'
    if (!TtlStash.spellVeto) throw "Iron's SpellPreCastEvent veto is not registered (see the startup log)"
    var got = TtlStash.spellRefused(TtlLife.dimensionOf(p), school)
    if (got !== want) throw `${p.username}: a ${school} cast in ${TtlLife.dimensionOf(p)} is ${got ? '' : 'not '}refused, expected ${want ? 'refused' : 'allowed'}`
    say(ctx, `stash ${p.username}: ${school} ${got ? 'refused' : 'allowed'} in ${TtlLife.dimensionOf(p)} as expected`)
    return 1
  }

  var clear = ctx => {
    var p = target(ctx)
    p.persistentData.remove(TtlStash.BANNED)
    p.persistentData.remove(TtlStash.KEEP)
    p.persistentData.remove(TtlStash.TOLD)
    TtlStash.extraSoulbound.length = 0
    say(ctx, `stash ${p.username}: cleared`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('stash')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .executes(logged(show))
        .then(Commands.literal('sweep').executes(logged(sweep)))
        .then(Commands.literal('clear').executes(logged(clear)))
        .then(Commands.literal('spell')
          .then(Commands.argument('school', Arguments.RESOURCE_LOCATION.create(event))
            .then(Commands.argument('refused', Arguments.STRING.create(event)).executes(logged(spell)))))
        .then(Commands.literal('equip')
          .then(Commands.argument('item', Arguments.RESOURCE_LOCATION.create(event)).executes(logged(equip))))
        .then(Commands.literal('soulbound')
          .then(Commands.argument('item', Arguments.RESOURCE_LOCATION.create(event)).executes(logged(soulbound))))
        .then(Commands.literal('expect')
          .then(Commands.argument('field', Arguments.STRING.create(event))
            .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(expect))))))))
})

// Iron's Spells veto (O-N1): see point 3 at the top. Registered once per script load.
try {
  var TtlSpellPreCastEvent = Java.loadClass('io.redspace.ironsspellbooks.api.events.SpellPreCastEvent')
  NativeEvents.onEvent(TtlSpellPreCastEvent, event => TtlStash.onSpellPreCast(event))
  TtlStash.spellVeto = true
  console.info("[ttl] stash: Iron's spell veto registered (mortal_banned.toml spell_schools)")
} catch (e) {
  console.error(`[ttl] stash: Iron's spell veto NOT registered, blood/eldritch casts stay possible in Life 1 (fallback: irons_spellbooks in mortal_banned.toml namespaces): ${e}`)
}
