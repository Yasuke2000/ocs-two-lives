// priority: 72
// Weapons and fighting behaviour of the generic NPCs (design/data/npc_gear.toml → TtlData.npc_gear; Yasuke 19/11/2026:
// "the guards have no weapons, also the npcs also do not, and don't defend themselves").
//
// Easy NPCs (sidequests.toml adventurers, companions, escort clients): their presets already carry the role's HandItems,
// zero drop chances and objectives (tools/gen_npcs.py). TtlSideNpc.spawn (sidequests/places.js) calls equipSide right
// after the import as well, so the hands are right even if a preset field is not read; companions.js equips its hire
// from the role too.
// Tempest residents (Tensura goblins, world/domains.js): `/summon` with NBT skips Tensura's own finalizeSpawn, so they
// came with empty hands. TtlDomains.mark calls ensureResident on every check and right after a respawn: a resident without
// the tag `ttl.gear.r<settings.rev>`, or whose hands are not its role's (a goblin picks up loot into its hand), gets its
// role's items (drop chance 0, CanPickUpLoot off) and, for a guard, the tag `ttl.npc.guard`.
// THE GUARD LOOP (every settings.guard_check_ticks, only while someone is online and Tempest is placed): a guard without a
// living target is set on the nearest foe (TtlNpcGear.foe: a monster by KubeJS isMonster() or an enemy of the roads,
// world/enemies.js; never a player, a resident, a guild or story NPC, a tame or owned creature, nor an entity with one of
// settings.guard_ignore_tags) within settings.guard_radius of its POST, so it defends the residents around it and does not
// wander off after a far mob. A guard with nothing to fight that strayed more than settings.guard_leash from its post walks
// back (teleported past 3 x the leash). Tensura's goblins think with SmartBrainLib: the target
// goes into their brain (BrainUtils.setTargetOfEntity), Mob.setTarget when that class cannot be loaded. Players only meet
// a guard's blade through Tensura's own retaliation (a soul that hits a resident), which kill_penalty.npc already prices
// (rep/guards.js).
// Commands (ops, /ttl npcgear ...): refresh · guards · testspawn <adventurer kind> <pos> · testclear ·
//   expect hand <resident id|test:<kind>> <main|off> <item|empty> · expect gone <entity tag> (test assertions: "ttl: ..."
//   when they do not hold).
const TtlNpcGear = {
  GUARD: 'ttl.npc.guard',
  GEAR: 'ttl.gear.r',
  TEST: 'ttl.test.gear',
  brainUtils: undefined,
  warned: false,
  last: { guards: 0, engaged: 0 },

  conf() {
    return TtlData.npc_gear || { settings: {}, role: [], ai: {}, residents: {} }
  },

  rev() {
    return Number(this.conf().settings.rev || 1)
  },

  role(id) {
    var all = this.conf().role || []
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  // The role of a Tempest resident record ({id, name}): its id, its lowercase name, else the unnamed goblins' role.
  residentRole(r) {
    var t = (this.conf().residents || {}).tempest || {}
    var name = String(r.name || '').toLowerCase()
    return this.role(t[String(r.id)] || (name && t[name]) || t.goblin)
  },

  uuid(e) {
    try {
      return String(e.uuid)
    } catch (x) {
      return ''
    }
  },

  // The role's items in both hands (empty hand = air), drop chance 0 for hands and armour, and no picking up loot: a
  // Tensura goblin takes what lies near it into its hand (staging 19/11/2026: Gobta with a bone, Rigur with leather).
  equip(server, e, role) {
    var id = this.uuid(e)
    if (!id || !role) return false
    TtlCmd.run(server, `item replace entity ${id} weapon.mainhand with ${role.main ? role.main : 'minecraft:air'}`)
    TtlCmd.run(server, `item replace entity ${id} weapon.offhand with ${role.off ? role.off : 'minecraft:air'}`)
    TtlCmd.run(server, `data merge entity ${id} {HandDropChances:[0.0f,0.0f],ArmorDropChances:[0.0f,0.0f,0.0f,0.0f],CanPickUpLoot:0b}`)
    return true
  },

  // The side kind behind a preset name (ttl_adv_<id>, ttl_comp_<id>, ttl_client_<id>), equipped with its role.
  equipSide(server, e, preset) {
    var m = /^ttl_(adv|comp|client)_([a-z0-9_]+)$/.exec(String(preset))
    if (!m) return false
    var list = (TtlData.sidequests || {})[m[1] === 'client' ? 'client' : 'adventurer'] || []
    for (var i = 0; i < list.length; i++) {
      if (String(list[i].id) === m[2]) return this.equip(server, e, this.role(list[i].role))
    }
    return false
  },

  // The item id in a hand ('' = empty).
  hand(e, off) {
    var stack = off ? e.getOffhandItem() : e.getMainHandItem()
    return stack && !stack.isEmpty() ? String(stack.id) : ''
  },

  holds(e, role) {
    return this.hand(e, false) === String(role.main || '') && this.hand(e, true) === String(role.off || '')
  },

  // TtlDomains.mark (every resident check and right after a respawn): the role's items whenever the hands are not
  // what the role says (a fresh summon, an item picked up, a rev bump) and the guard tag.
  ensureResident(e, r) {
    var tags = e.getTags()
    var mine = this.GEAR + this.rev()
    var role = this.residentRole(r)
    if (!role) return
    if (tags.contains(mine) && this.holds(e, role)) return
    var server = e.getServer()
    if (!server) return
    this.equip(server, e, role)
    var old = []
    var prefix = this.GEAR
    tags.forEach(t => { if (String(t).indexOf(prefix) === 0) old.push(String(t)) })
    old.forEach(t => e.removeTag(t))
    if (String(role.ai) === 'guard') e.addTag(this.GUARD)
    else e.removeTag(this.GUARD)
    e.addTag(mine)
  },

  ignored(e) {
    var skip = this.conf().settings.guard_ignore_tags || []
    var tags = e.getTags()
    for (var i = 0; i < skip.length; i++) {
      if (tags.contains(String(skip[i]))) return true
    }
    return false
  },

  // Somebody's own creature (a Tensura tame, a named monster, a wolf): never a guard's foe, whatever isMonster() says.
  owned(e) {
    try {
      if (typeof e.isTame === 'function' && e.isTame()) return true
    } catch (x) {
      // not tameable
    }
    try {
      if (typeof e.getOwnerUUID === 'function' && e.getOwnerUUID()) return true
    } catch (x) {
      // no owner
    }
    return false
  },

  // A guard's foe: a monster (an Enemy) or one of the enemies of the roads (world/enemies.js, Easy NPCs: not Enemy), never a
  // player, a resident, a guild or story NPC, a tame or anything with a guard_ignore_tags tag.
  foe(e) {
    var tags = e.getTags()
    if (tags.contains(this.GUARD) || tags.contains('ttl_tempest_resident') || tags.contains('ttl.npc')) return false
    if (!(e.isMonster() || tags.contains('ttl.enemy'))) return false
    return !this.ignored(e) && !this.owned(e)
  },

  utils() {
    if (this.brainUtils === undefined) {
      try {
        this.brainUtils = Java.loadClass('net.tslat.smartbrainlib.util.BrainUtils')
      } catch (x) {
        this.brainUtils = null
        console.warn(`[ttl] npc gear: SmartBrainLib's BrainUtils cannot be loaded (${x}); guards fall back to Mob.setTarget`)
      }
    }
    return this.brainUtils
  },

  targetOf(e) {
    var u = this.utils()
    try {
      return u ? u.getTargetOfEntity(e) : e.getTarget()
    } catch (x) {
      return null
    }
  },

  aim(e, target) {
    var u = this.utils()
    try {
      if (u) u.setTargetOfEntity(e, target)
      else e.setTarget(target)
      return true
    } catch (x) {
      if (!this.warned) console.warn(`[ttl] npc gear: could not set guard ${String(e.type)} on ${String(target.type)} (${x})`)
      this.warned = true
      return false
    }
  },

  // One pass of the guard loop. Returns {guards, engaged}.
  guardPass(server) {
    var out = { guards: 0, engaged: 0 }
    if (typeof TtlDomains === 'undefined') return out
    var posts = {}
    var list = TtlDomains.residents(server)
    if (!list.length) return out
    var radius = Number(this.conf().settings.guard_radius || 16)
    var x0 = Infinity, z0 = Infinity, x1 = -Infinity, z1 = -Infinity, y = 0
    list.forEach(r => {
      posts[r.id] = r
      x0 = Math.min(x0, r.x); z0 = Math.min(z0, r.z); x1 = Math.max(x1, r.x); z1 = Math.max(z1, r.z); y = r.y
    })
    var level = server.getLevel(list[0].dim)
    if (!level) return out
    var AABB = Java.loadClass('net.minecraft.world.phys.AABB')
    var guards = []
    var foes = []
    var self = this
    var leash = Number(this.conf().settings.guard_leash || 0)
    level.getEntitiesWithin(new AABB(x0 - radius - leash * 3, y - 24, z0 - radius - leash * 3, x1 + radius + leash * 3, y + 24, z1 + radius + leash * 3)).forEach(e => {
      if (!e.isAlive() || e.isPlayer()) return
      if (e.getTags().contains(self.GUARD)) guards.push(e)
      else if (self.foe(e)) foes.push(e)
    })
    out.guards = guards.length
    out.away = 0
    guards.forEach(g => {
      var cur = self.targetOf(g)
      if (cur && cur.isAlive()) return
      var post = posts[TtlDomains.residentId(g)]
      if (!post) return
      // Back to the post when it wandered off with nothing to fight (Tensura's goblins stroll; the guard loop only
      // defends within guard_radius of the post).
      var hx = g.getX() - post.x
      var hz = g.getZ() - post.z
      var off = Math.sqrt(hx * hx + hz * hz)
      if (leash > 0 && off > leash) {
        out.away++
        try {
          if (off > 3 * leash) g.teleportTo(post.x + 0.5, post.y, post.z + 0.5)
          else g.getNavigation().moveTo(post.x + 0.5, post.y, post.z + 0.5, 1.0)
        } catch (x) {
          if (!self.warned) console.warn(`[ttl] npc gear: could not send guard ${TtlDomains.residentId(g)} back to its post (${x})`)
          self.warned = true
        }
      }
    })
    if (!foes.length) {
      this.last = out
      return out
    }
    guards.forEach(g => {
      var cur = self.targetOf(g)
      if (cur && cur.isAlive()) return
      var post = posts[TtlDomains.residentId(g)]
      if (!post) return
      var best = null
      var bestD = Infinity
      foes.forEach(f => {
        var px = f.getX() - post.x
        var pz = f.getZ() - post.z
        if (px * px + pz * pz > radius * radius) return
        var dx = f.getX() - g.getX()
        var dz = f.getZ() - g.getZ()
        var d = dx * dx + dz * dz
        if (d < bestD) {
          best = f
          bestD = d
        }
      })
      if (best && self.aim(g, best)) out.engaged++
    })
    this.last = out
    return out
  }
}

// Tensura's humanoids drop every equipment slot on death whatever the drop chance (TensuraHumanoidEntity.dropEquipment),
// so the role items of a geared NPC are taken out of its drops here; whatever else it drops (Tensura's loot) stays.
EntityEvents.drops(event => {
  try {
    var e = event.entity
    var tags = e.getTags()
    var geared = false
    tags.forEach(t => {
      var s = String(t)
      if (s.indexOf(TtlNpcGear.GEAR) === 0 || s === 'ttl.adv' || s === 'ttl.comp' || s === 'ttl.side.client' || s === TtlNpcGear.TEST) geared = true
    })
    if (!geared) return
    var gear = {}
    ;(TtlNpcGear.conf().role || []).forEach(r => {
      if (r.main) gear[String(r.main)] = true
      if (r.off) gear[String(r.off)] = true
    })
    var drops = event.getDrops()
    var gone = []
    drops.forEach(d => {
      var id = String(d.getItem().id)
      if (gear[id] || (tags.contains('ttl.comp') && /_(helmet|chestplate|leggings|boots)$/.test(id))) gone.push(d)
    })
    gone.forEach(d => drops.remove(d))
  } catch (x) {
    console.error(`[ttl] npc gear: drop filter failed: ${x}`)
  }
})

ServerEvents.loaded(event => {
  var server = event.server
  var every = Math.max(20, Number(TtlNpcGear.conf().settings.guard_check_ticks || 40))
  var loop = () => server.scheduleInTicks(every, () => {
    try {
      if (server.getPlayerList().getPlayers().size() > 0) TtlNpcGear.guardPass(server)
    } catch (e) {
      console.error(`[ttl] npc gear: guard pass failed: ${e}`)
    }
    loop()
  })
  loop()
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var ops = src => src.hasPermission(2)
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] npc gear command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var server = ctx => ctx.source.getServer()

  var byTag = (s, tag) => {
    var found = null
    s.getAllLevels().forEach(level => {
      level.getEntities().forEach(e => {
        if (!found && e.isAlive() && e.getTags().contains(tag)) found = e
      })
    })
    return found
  }

  var refresh = ctx => {
    var s = server(ctx)
    var n = 0
    s.getAllLevels().forEach(level => {
      level.getEntities().forEach(e => {
        if (!e.getTags().contains(TtlDomains.RESIDENT)) return
        e.removeTag(TtlNpcGear.GEAR + TtlNpcGear.rev())
        n++
      })
    })
    TtlDomains.ensureResidents(s)
    say(ctx, `npc gear: ${n} resident(s) re-equipped (rev ${TtlNpcGear.rev()})`)
    return 1
  }

  var guards = ctx => {
    var r = TtlNpcGear.guardPass(server(ctx))
    say(ctx, `npc gear: ${r.guards} guard(s) near their posts, ${r.engaged} set on a foe, ${r.away || 0} sent back to their post`)
    return 1
  }

  var testspawn = ctx => {
    var s = server(ctx)
    var kind = String(Arguments.STRING.getResult(ctx, 'kind'))
    var bp = Arguments.BLOCK_POS.getResult(ctx, 'pos')
    var pos = { dim: String(ctx.source.getLevel().dimension), x: bp.getX() + 0.5, y: bp.getY(), z: bp.getZ() + 0.5 }
    var e = TtlSideNpc.spawn(s, pos, `ttl_adv_${kind}`, [TtlNpcGear.TEST, `${TtlNpcGear.TEST}.${kind}`])
    if (!e) throw `could not import ttl_adv_${kind}`
    say(ctx, `npc gear: test adventurer ${kind} at ${pos.x} ${pos.y} ${pos.z}`)
    return 1
  }

  var testclear = ctx => {
    var s = server(ctx)
    var list = []
    s.getAllLevels().forEach(level => level.getEntities().forEach(e => { if (e.getTags().contains(TtlNpcGear.TEST)) list.push(e) }))
    list.forEach(e => TtlSideNpc.remove(s, e))
    say(ctx, `npc gear: ${list.length} test NPC(s) removed`)
    return 1
  }

  var expect = ctx => {
    var s = server(ctx)
    var parts = String(Arguments.GREEDY_STRING.getResult(ctx, 'what')).trim().split(/\s+/)
    if (parts[0] === 'gone' && parts.length === 2) {
      var left = byTag(s, parts[1])
      if (left) throw `npc gear: expected no living entity tagged ${parts[1]}, ${String(left.type)} is still alive`
      say(ctx, `npc gear: nothing tagged ${parts[1]} alive, as expected`)
      return 1
    }
    if (parts[0] === 'hand' && parts.length === 4) {
      var who = parts[1].indexOf('test:') === 0 ? `${TtlNpcGear.TEST}.${parts[1].slice(5)}` : `${TtlDomains.RES_TAG}${parts[1]}`
      var e = byTag(s, who)
      if (!e) throw `npc gear: no living entity tagged ${who}`
      var stack = parts[2] === 'off' ? e.getOffhandItem() : e.getMainHandItem()
      var got = stack && !stack.isEmpty() ? String(stack.id) : 'empty'
      if (got !== parts[3]) throw `npc gear: expected ${parts[1]} ${parts[2]} hand ${parts[3]}, got ${got}`
      say(ctx, `npc gear: ${parts[1]} ${parts[2]} hand ${got} as expected`)
      return 1
    }
    throw 'expect hand <resident id|test:<kind>> <main|off> <item|empty> · expect gone <entity tag>'
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('npcgear').requires(ops)
      .then(Commands.literal('refresh').executes(logged(refresh)))
      .then(Commands.literal('guards').executes(logged(guards)))
      .then(Commands.literal('testspawn').then(Commands.argument('kind', Arguments.STRING.create(event))
        .then(Commands.argument('pos', Arguments.BLOCK_POS.create(event)).executes(logged(testspawn)))))
      .then(Commands.literal('testclear').executes(logged(testclear)))
      .then(Commands.literal('expect').then(Commands.argument('what', Arguments.GREEDY_STRING.create(event)).executes(logged(expect))))))
})
