// priority: 67
// Moral-choice scenes 4.1-4.4 (design/architecture/paths-necro-artificer.md §4; WP-C1). Engine and API: choices/engine.js.
// Numbers, texts and costs: design/data/choices.toml ([[choice]] sick_village, bandit_hostages, starving_band, wants_name).
// Our interpretation of the design, kept simple enough to test with bots:
//   4.1 sick_village     vanilla villagers (NoAI, Invulnerable: no mob or stray blow decides the scene), Weakness + Slowness,
//                        health start_health. Healing = their health reaching cure_at by ANY heal (a Hipokute Salve right-
//                        click, a splash potion of healing, Iron's or Tensura's healing magic: we read the health, not the
//                        source; the soul nearest the villager is the healer). Release (dark, a menu route for necromancers):
//                        they die, ash_each soul ash per villager; a necromancer with a Bone Altar and room raises them there
//                        at once through TtlLegion.raise (each raise is its own necro.raise dark act).
//   4.2 bandit_hostages  hostile tensura:orc bandits + a captain; hostages are NoAI, Invulnerable villagers. Rescue = the
//                        bandits and the captain dead, then each hostage's bonds cut (right-click). Pay (grey) and Take (dark,
//                        kill the hostages and loot) are menu routes that need the captain alive. The escort to a road
//                        (design: escort kind) is WP-C2's `escort-to` kind; here the freed hostages go home by themselves.
//   4.3 starving_band    NoAI tensura:orc (tag ttl.horde) at a ttl:offering_bowl; feed = food_each food items per orc into
//                        the bowl (right-click it with food); devour (dark) = the band killed by players; absorb (grey,
//                        Tensura's own mechanic is not punished twice) = a menu route for Predator/Gluttony/Starved holders
//                        that adds the band's EP x ep_mult through `tensura edit stat`. Enslaving by Dominate: later (C2).
//   4.4 wants_name       one NoAI Tensura beast at start_pct health (tag ttl.wants_name). Name (good) = Tensura's own
//                        naming gives it a name and a permanent owner (IExistence); bind (dark) = a temporary owner without
//                        a name (Dominate); slay (dark) = killed by a player (a necromancer takes ash_slay soul ash).
//                        A named or bound beast stays (its scene tags are removed, NoAI off).
// Test verbs (/ttl choice test <player> <verb> <sid> [n]): heal [n] (sick villagers or the beast, full health, the player
// is the healer), free (every hostage, the camp must be clear), feed <n>, kill <role> (the player is the last attacker),
// owner name|bind (the beast's Tensura owner as if named/dominated by the player; Tensura's real state is read as well).
const TtlChoicesC1 = {
  OVERWORLD: 'minecraft:overworld',
  food: undefined,

  ring(n, r0, r1, i) {
    var a = (2 * Math.PI * i) / Math.max(1, n) + Math.random() * 0.4
    var r = r0 + Math.random() * (r1 - r0)
    return { dx: Math.round(Math.cos(a) * r), dz: Math.round(Math.sin(a) * r) }
  },

  hasTag(e, t) {
    try {
      return e.getTags().contains(t)
    } catch (err) {
      return false
    }
  },

  heal(e, n) {
    try {
      e.setHealth(Math.min(Number(e.getMaxHealth()), Number(e.getHealth()) + Number(n)))
    } catch (err) {
      console.warn(`[ttl] choices: heal failed: ${err}`)
    }
  },

  setPct(e, pct) {
    try {
      e.setHealth(Math.max(1, Number(e.getMaxHealth()) * Number(pct)))
    } catch (err) {
      console.warn(`[ttl] choices: health set failed: ${err}`)
    }
  },

  healer(e) {
    try {
      return String(e.persistentData.getString('ttl.healer') || '')
    } catch (err) {
      return ''
    }
  },

  markHealer(e, player) {
    try {
      e.persistentData.putString('ttl.healer', String(player.username))
    } catch (err) {
      // the nearest soul is the healer then
    }
  },

  // The name with the highest count in {name: n}, '' when empty.
  top(table) {
    var best = ''
    var n = -1
    Object.keys(table || {}).forEach(k => {
      if (Number(table[k]) > n) {
        n = Number(table[k])
        best = k
      }
    })
    return best
  },

  bump(table, name, n) {
    table[name] = Number(table[name] || 0) + Number(n === undefined ? 1 : n)
  },

  isFood(stack) {
    if (!stack || stack.isEmpty()) return false
    if (this.food === undefined) {
      try {
        this.food = Java.loadClass('net.minecraft.core.component.DataComponents').FOOD
      } catch (e) {
        this.food = null
      }
    }
    try {
      if (this.food && stack.has(this.food)) return true
    } catch (e) {
      // try the tag
    }
    try {
      return !!stack.hasTag('c:foods')
    } catch (e) {
      return false
    }
  },

  byUuid(server, uuid) {
    if (!uuid) return null
    var found = null
    server.getPlayerList().getPlayers().forEach(p => {
      if (!found && TtlLife.uuid(p) === String(uuid)) found = p
    })
    return found
  },

  // Keeps a scene entity in the world after the scene: no scene tags, AI on, persistent.
  clearEffects(e) {
    try {
      e.removeAllEffects()
    } catch (err) {
      console.warn(`[ttl] choices: effects not cleared: ${err}`)
    }
  },

  release(ctx, e) {
    try {
      e.setNoAi(false)
      e.setPersistenceRequired()
    } catch (err) {
      console.warn(`[ttl] choices: a kept scene entity keeps NoAI: ${err}`)
    }
    TtlChoices.tagsOf(e).forEach(t => {
      if (t === 'ttl.scene' || t.indexOf('ttl.scene.') === 0 || t.indexOf('ttl.role.') === 0) e.removeTag(t)
    })
  },

  // A necromancer's dead rise at once at one of their Bone Altars (WP-N2, guarded): ash is given first, raise spends it.
  raiseAtAltar(server, player, n, label) {
    var raised = 0
    try {
      if (typeof TtlLegion === 'undefined' || TtlLegion.rank(player) < 1) return 0
      var altars = TtlLegion.altarsOf(server, TtlLife.uuid(player))
      if (!altars.length) return 0
      for (var i = 0; i < n; i++) {
        var res = TtlLegion.raise(server, player, 'zombie', 'ash', label, { altar: altars[0].key })
        if (!res || !res.ok || res.queued) break
        raised++
      }
    } catch (e) {
      console.error(`[ttl] choices: raising at ${player.username}'s altar failed: ${e}`)
    }
    return raised
  }
}

// ---- 4.1 the sick village ----------------------------------------------------------------------------------------------

TtlChoices.register({
  id: 'sick_village',

  spawn(server, scene, ctx) {
    ctx.place(0, 0, 0, 'minecraft:campfire')
    ;[[4, 3], [-4, 2], [1, -5]].forEach(p => ctx.place(p[0], 0, p[1], 'minecraft:hay_block'))
    var n = ctx.count('villagers')
    for (var i = 0; i < n; i++) {
      var o = TtlChoicesC1.ring(n, 2, 5, i)
      ctx.summon('villagers', 'minecraft:villager', o.dx, o.dz, ['NoAI:1b', 'Invulnerable:1b', `Health:${Number(ctx.knob('start_health', 6))}f`], 'Sick villager')
    }
    if (!scene.n.villagers) return false
    ctx.cmd(`effect give ${ctx.sel('villagers')} minecraft:weakness infinite 0 true`)
    ctx.cmd(`effect give ${ctx.sel('villagers')} minecraft:slowness infinite 1 true`)
    scene.prog.cured = 0
    scene.prog.healers = {}
  },

  poll(server, scene, ctx) {
    ctx.cmd(`particle minecraft:spore_blossom_air ${scene.x} ${scene.y + 1} ${scene.z} 4 1 4 0 30`)
    var cureAt = Number(ctx.knob('cure_at', 16))
    var reach = Number(ctx.knob('heal_reach', 8))
    var list = ctx.alive('villagers')
    list.forEach(e => {
      if (TtlChoicesC1.hasTag(e, 'ttl.cured') || Number(e.getHealth()) < cureAt) return
      e.addTag('ttl.cured')
      var name = TtlChoicesC1.healer(e)
      var p = name ? server.getPlayerList().getPlayerByName(name) : null
      if (!p) p = ctx.nearest(e.getX(), e.getY(), e.getZ(), reach)
      if (p) {
        ctx.part(p, 'healed')
        TtlChoicesC1.bump(scene.prog.healers, String(p.username))
      }
      TtlChoicesC1.clearEffects(e)
      ctx.cmd(`particle minecraft:happy_villager ${e.getX()} ${e.getY() + 1} ${e.getZ()} 0.4 0.6 0.4 0 12`)
    })
    scene.prog.cured = list.filter(e => TtlChoicesC1.hasTag(e, 'ttl.cured')).length
    if (list.length > 0 && scene.prog.cured >= list.length) ctx.resolve('heal', TtlChoicesC1.top(scene.prog.healers))
  },

  interact(server, scene, player, e, item, ctx) {
    if (TtlChoicesC1.hasTag(e, 'ttl.cured')) {
      player.tell(Text.gray('This one is well again.'))
      return true
    }
    if (String(item.id) === 'ttl:hipokute_salve') {
      item.shrink(1)
      TtlChoicesC1.heal(e, Number(ctx.knob('salve_heal', 5)))
      TtlChoicesC1.markHealer(e, player)
      ctx.part(player, 'healed')
      player.tell(Text.green(`The salve eases the fever (${Math.round(e.getHealth())}/${Math.round(e.getMaxHealth())}).`))
    } else {
      player.tell(Text.gray('The villager is burning with fever. A Hipokute Salve, a healing spell or a potion of healing would help.'))
    }
    return true
  },

  routes: {
    release: {
      take(server, scene, player, ctx) {
        var n = ctx.alive('villagers').length
        if (n < 1) return 'there is nobody left to release'
        ctx.cmd(`particle minecraft:soul ${scene.x} ${scene.y + 1} ${scene.z} 3 1 3 0.02 60`)
        ctx.cmd(`kill ${ctx.sel('villagers')}`)
        ctx.give(player, 'ttl:soul_ash', n * Number(ctx.knob('ash_each', 2)))
        scene.prog.released = n
        scene.prog.raised = TtlChoicesC1.raiseAtAltar(server, player, n, 'Plague-born')
        if (scene.prog.raised > 0) player.tell(Text.darkPurple(`${scene.prog.raised} of them rise at your Bone Altar.`))
        return ''
      }
    }
  },

  resolved(server, scene, rid, actor, ctx) {
    if (rid === 'heal') ctx.cmd(`particle minecraft:happy_villager ${scene.x} ${scene.y + 1} ${scene.z} 4 1 4 0 40`)
  },

  neutral(server, scene, ctx) {
    ctx.cmd(`kill ${ctx.sel('villagers')}`)
  },

  test(server, scene, player, verb, arg, ctx) {
    if (verb !== 'heal') return 'sick_village test verbs: heal [n]'
    var n = Math.max(1, Number(arg || 1))
    var left = ctx.alive('villagers').filter(e => !TtlChoicesC1.hasTag(e, 'ttl.cured'))
    left.slice(0, n).forEach(e => {
      TtlChoicesC1.heal(e, 100)
      TtlChoicesC1.markHealer(e, player)
      ctx.part(player, 'healed')
    })
    return left.length ? '' : 'nobody left to heal'
  }
})

// ---- 4.2 bandit hostages ---------------------------------------------------------------------------------------------

TtlChoices.register({
  id: 'bandit_hostages',

  spawn(server, scene, ctx) {
    ctx.place(0, 0, 0, 'minecraft:campfire')
    var h = ctx.count('hostages')
    for (var i = 0; i < h; i++) {
      var o = TtlChoicesC1.ring(h, 1, 2, i)
      ctx.summon('hostages', 'minecraft:villager', o.dx, o.dz, ['NoAI:1b', 'Invulnerable:1b'], 'Hostage')
    }
    var b = ctx.count('bandits')
    for (var j = 0; j < b; j++) {
      var q = TtlChoicesC1.ring(b, 5, 8, j)
      ctx.summon('bandits', 'tensura:orc', q.dx, q.dz, [], 'Bandit')
    }
    ctx.summon('captain', 'tensura:orc', 3, 0, [], 'Bandit Captain')
    if (!scene.n.hostages || !scene.n.captain) return false
    ctx.cmd(`attribute ${ctx.one('captain')} minecraft:generic.max_health base set ${Number(ctx.knob('captain_health', 60))}`)
    ctx.alive('captain').forEach(e => TtlChoicesC1.setPct(e, 1))
    scene.prog.cleared = false
    scene.prog.freed = 0
  },

  poll(server, scene, ctx) {
    if (!scene.prog.cleared && ctx.alive('bandits').length === 0 && ctx.alive('captain').length === 0) {
      scene.prog.cleared = true
      ctx.say('The bandit camp is cleared. Cut the hostages\' bonds (right-click each one).', TtlChoices.eng().credit_radius)
    }
    var hostages = ctx.alive('hostages')
    scene.prog.freed = hostages.filter(e => TtlChoicesC1.hasTag(e, 'ttl.freed')).length
    if (scene.prog.cleared && hostages.length > 0 && scene.prog.freed >= hostages.length) ctx.resolve('rescue', String(scene.prog.lastFreer || ''))
  },

  interact(server, scene, player, e, item, ctx) {
    if (TtlChoices.roleOf(e) !== 'hostages') return false
    if (!scene.prog.cleared) {
      player.tell(Text.gray('The bandits are watching. Clear the camp first, or make the captain an offer: /ttl choice'))
      return true
    }
    if (!TtlChoicesC1.hasTag(e, 'ttl.freed')) {
      e.addTag('ttl.freed')
      ctx.part(player, 'freed')
      scene.prog.lastFreer = String(player.username)
      player.tell(Text.green('You cut the bonds. "Thank you, thank you!"'))
    }
    return true
  },

  routes: {
    pay: {
      need(server, scene, player, ctx) {
        return ctx.alive('captain').length ? '' : 'the captain is dead: there is nobody left to pay'
      },
      take(server, scene, player, ctx) {
        ctx.alive('bandits').concat(ctx.alive('captain')).forEach(e => e.discard())
        ctx.alive('hostages').forEach(e => e.addTag('ttl.freed'))
        return ''
      }
    },
    take: {
      need(server, scene, player, ctx) {
        return ctx.alive('captain').length ? '' : 'the captain is dead: there is no deal to make'
      },
      take(server, scene, player, ctx) {
        var n = ctx.alive('hostages').length
        if (n < 1) return 'there are no hostages left'
        ctx.cmd(`kill ${ctx.sel('hostages')}`)
        ctx.give(player, 'ttl:soul_ash', n * Number(ctx.knob('ash_each', 1)))
        var silver = Math.floor(Number(ctx.knob('loot_silver', 8)) * Number(scene.mult || 1))
        try {
          if (typeof TtlEcon !== 'undefined' && silver > 0) TtlEcon.pay(server, player, { silver: silver }, 'choice bandit_hostages loot')
        } catch (e) {
          console.error(`[ttl] choices: bandit loot for ${player.username} failed: ${e}`)
        }
        scene.prog.killed = n
        return ''
      }
    }
  },

  resolved(server, scene, rid, actor, ctx) {
    if (rid !== 'take') ctx.cmd(`particle minecraft:happy_villager ${scene.x} ${scene.y + 1} ${scene.z} 2 1 2 0 20`)
  },

  neutral(server, scene, ctx) {
    ctx.entities('').forEach(e => { if (TtlChoices.roleOf(e) !== 'anchor') e.discard() })
  },

  test(server, scene, player, verb, arg, ctx) {
    if (verb === 'free') {
      if (!scene.prog.cleared) return 'the camp is not cleared'
      ctx.alive('hostages').forEach(e => e.addTag('ttl.freed'))
      ctx.part(player, 'freed')
      scene.prog.lastFreer = String(player.username)
      return ''
    }
    if (verb === 'kill') return TtlChoicesC1.testKill(scene, player, arg, ctx)
    return 'bandit_hostages test verbs: kill <role>, free'
  }
})

// ---- 4.3 the starving band -------------------------------------------------------------------------------------------

TtlChoices.register({
  id: 'starving_band',

  spawn(server, scene, ctx) {
    var bowl = ctx.place(0, 0, 0, 'ttl:offering_bowl')
    if (!bowl) return false
    scene.prog.bowl = [bowl.x, bowl.y, bowl.z]
    ;[[3, 3], [-3, 3], [3, -3]].forEach(p => ctx.place(p[0], 0, p[1], 'minecraft:hay_block'))
    var n = ctx.count('orcs')
    for (var i = 0; i < n; i++) {
      var o = TtlChoicesC1.ring(n, 2, 4, i)
      ctx.summon('orcs', 'tensura:orc', o.dx, o.dz, { parts: ['NoAI:1b'], tags: ['ttl.horde'] }, 'Starving orc')
    }
    if (!scene.n.orcs) return false
    ctx.alive('orcs').forEach(e => TtlChoicesC1.setPct(e, 0.5))
    ctx.cmd(`effect give ${ctx.sel('orcs')} minecraft:slowness infinite 1 true`)
    scene.prog.food = 0
    scene.prog.need = scene.n.orcs * Number(ctx.knob('food_each', 6))
    scene.prog.feeders = {}
  },

  poll(server, scene, ctx) {
    if (Number(scene.prog.food) >= Number(scene.prog.need)) {
      ctx.resolve('feed', TtlChoicesC1.top(scene.prog.feeders))
      return
    }
    if (ctx.alive('orcs').length > 0) return
    if (scene.hits.orcs) ctx.resolve('devour', String(scene.hits.orcs))
    else TtlChoices.neutral(server, scene.sid, 'the band died')
  },

  useBlock(server, scene, player, block, item, ctx) {
    if (!TtlChoicesC1.isFood(item)) {
      player.tell(Text.gray(`The bowl is empty. The orcs need food: ${scene.prog.food}/${scene.prog.need}.`))
      return true
    }
    var k = Math.min(Number(item.count), Number(scene.prog.need) - Number(scene.prog.food))
    if (k <= 0) return true
    item.shrink(k)
    scene.prog.food = Number(scene.prog.food) + k
    TtlChoicesC1.bump(scene.prog.feeders, String(player.username), k)
    ctx.part(player, 'fed')
    player.tell(Text.green(`The orcs eat (${scene.prog.food}/${scene.prog.need}).`))
    if (Number(scene.prog.food) >= Number(scene.prog.need)) ctx.resolve('feed', TtlChoicesC1.top(scene.prog.feeders))
    return true
  },

  routes: {
    absorb: {
      need(server, scene, player, ctx) {
        return ctx.alive('orcs').length ? '' : 'there is nothing left to devour'
      },
      take(server, scene, player, ctx) {
        var ep = 0
        var fallback = Number(ctx.knob('ep_fallback', 2000))
        ctx.alive('orcs').forEach(e => {
          var x = TtlChoices.existence(e)
          var v = 0
          try {
            v = x ? Number(x.getEP()) : 0
          } catch (err) {
            v = 0
          }
          ep += v > 0 ? v : fallback
          e.discard()
        })
        ep = Math.floor(ep * Number(ctx.knob('ep_mult', 2)))
        scene.prog.ep = ep
        if (ep > 0 && !TtlCmd.run(server, `tensura edit stat ${player.username} ep current add ${ep}`)) console.warn(`[ttl] choices: Tensura did not take +${ep} EP for ${player.username}`)
        ctx.cmd(`particle minecraft:large_smoke ${scene.x} ${scene.y + 1} ${scene.z} 2 1 2 0.02 40`)
        return ''
      }
    }
  },

  neutral(server, scene, ctx) {
    ctx.alive('orcs').forEach(e => e.discard())
  },

  test(server, scene, player, verb, arg, ctx) {
    if (verb === 'feed') {
      var n = Math.max(1, Number(arg || 1))
      scene.prog.food = Math.min(Number(scene.prog.need), Number(scene.prog.food) + n)
      TtlChoicesC1.bump(scene.prog.feeders, String(player.username), n)
      ctx.part(player, 'fed')
      return ''
    }
    if (verb === 'kill') return TtlChoicesC1.testKill(scene, player, arg, ctx)
    return 'starving_band test verbs: feed <n>, kill orcs'
  }
})

// ---- 4.4 a wounded monster wants a name ------------------------------------------------------------------------------

TtlChoices.register({
  id: 'wants_name',

  spawn(server, scene, ctx) {
    var types = ctx.knob('types', ['tensura:direwolf'])
    var type = String(types[Math.floor(Math.random() * types.length)])
    scene.prog.type = type
    if (!ctx.summon('beast', type, 0, 0, { parts: ['NoAI:1b'], tags: ['ttl.wants_name'] }, '')) return false
    ctx.alive('beast').forEach(e => TtlChoicesC1.setPct(e, Number(ctx.knob('start_pct', 0.1))))
    ctx.cmd(`effect give ${ctx.sel('beast')} minecraft:weakness infinite 0 true`)
    scene.prog.healed = false
  },

  poll(server, scene, ctx) {
    var list = ctx.alive('beast')
    if (!list.length) {
      if (scene.hits.beast) ctx.resolve('slay', String(scene.hits.beast))
      else TtlChoices.neutral(server, scene.sid, 'the beast died')
      return
    }
    var e = list[0]
    if (!scene.prog.healed && Number(e.getHealth()) >= Number(e.getMaxHealth()) * Number(ctx.knob('healed_pct', 0.5))) {
      scene.prog.healed = true
      var name = TtlChoicesC1.healer(e)
      var p = name ? server.getPlayerList().getPlayerByName(name) : ctx.nearest(e.getX(), e.getY(), e.getZ(), 8)
      if (p) ctx.part(p, 'healed')
      ctx.say('The monster stands, unsteady. It is waiting for a name.', TtlChoices.eng().notice_radius)
    }
    var named = ''
    var perm = ''
    var temp = ''
    var x = TtlChoices.existence(e)
    try {
      if (x) {
        named = x.getName() ? String(x.getName()) : ''
        perm = x.getPermanentOwner() ? String(x.getPermanentOwner()) : ''
        temp = x.getTemporaryOwner() ? String(x.getTemporaryOwner()) : ''
      }
    } catch (err) {
      console.warn(`[ttl] choices: reading the beast's Tensura owner failed: ${err}`)
    }
    var fake = scene.prog.fake
    if (fake && fake.named) {
      named = named || 'test'
      perm = fake.uuid
    } else if (fake) {
      temp = fake.uuid
    }
    if (named && perm) {
      var owner = TtlChoicesC1.byUuid(server, perm)
      if (owner) {
        ctx.part(owner, 'named')
        ctx.resolve('name', String(owner.username))
      }
      return
    }
    var by = TtlChoicesC1.byUuid(server, temp || perm)
    if (by) {
      ctx.part(by, 'bound')
      ctx.resolve('bind', String(by.username))
    }
  },

  // Only the salve is ours; every other right-click (Tensura's naming) goes through.
  interact(server, scene, player, e, item, ctx) {
    if (String(item.id) !== 'ttl:hipokute_salve') return false
    item.shrink(1)
    TtlChoicesC1.heal(e, Number(ctx.knob('salve_heal', 8)))
    TtlChoicesC1.markHealer(e, player)
    ctx.part(player, 'healed')
    player.tell(Text.green(`The salve closes its wounds (${Math.round(e.getHealth())}/${Math.round(e.getMaxHealth())}).`))
    return true
  },

  resolved(server, scene, rid, actor, ctx) {
    if (rid === 'name' || rid === 'bind') {
      ctx.alive('beast').forEach(e => {
        TtlChoicesC1.clearEffects(e)
        TtlChoicesC1.release(ctx, e)
      })
    } else if (rid === 'slay') {
      var p = server.getPlayerList().getPlayerByName(String(actor))
      if (p && TtlChoices.isNecro(p)) ctx.give(p, 'ttl:soul_ash', Number(ctx.knob('ash_slay', 1)))
    }
  },

  neutral(server, scene, ctx) {
    ctx.alive('beast').forEach(e => e.discard())
  },

  test(server, scene, player, verb, arg, ctx) {
    if (verb === 'heal') {
      ctx.alive('beast').forEach(e => {
        TtlChoicesC1.heal(e, 1000)
        TtlChoicesC1.markHealer(e, player)
      })
      ctx.part(player, 'healed')
      return ''
    }
    if (verb === 'owner') {
      scene.prog.fake = { uuid: TtlLife.uuid(player), named: String(arg) !== 'bind' }
      return ''
    }
    if (verb === 'kill') return TtlChoicesC1.testKill(scene, player, arg || 'beast', ctx)
    return 'wants_name test verbs: heal, owner name|bind, kill'
  }
})

// Test: `player` is the last attacker of every entity of a role, and they die (as if it had killed them).
TtlChoicesC1.testKill = function (scene, player, role, ctx) {
  role = String(role || '')
  if (!role || role === 'anchor') return 'kill <role>'
  if (!ctx.alive(role).length) return `no ${role} alive`
  scene.hits[role] = String(player.username)
  ctx.part(player, 'hit')
  ctx.cmd(`kill ${ctx.sel(role)}`)
  return ''
}
