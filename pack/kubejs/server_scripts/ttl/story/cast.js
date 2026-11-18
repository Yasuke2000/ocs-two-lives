// priority: 40
// The story cast in the world (WP-S4, design/architecture/story-characters.md §1, §6.2; data: design/data/npcs.toml, words: story.toml).
// Placement itself is economy/guild_npcs.js (one entity per active spot, found by tags, spawned only into a loaded chunk); this
// file adds what the cast needs on top of the guild NPCs:
//   1. STATUES. A [[kind]] with `statue = "<entity id>"` is the mod's own character entity (Tensura / NEB) standing as a tame,
//      NoAI, invulnerable, silent, persistent statue: the throne-Gazel pattern of life/dwargon.js (a dummy Owner makes the
//      entity tame, so a right-click does not wake it and it never starts the fight of its boss twin). Rule R1: a character a
//      mod has is never rebuilt as an Easy NPC. TtlCast.spawnStatue is what guild_npcs.js calls for such a spot.
//   2. THE RIGHT-CLICK. A statue (tag `ttl.talk.<story npc id>`) and every entity named by a [[hook]] (the throne Gazel, the
//      named goblins Rigurd and Gobta of Tempest) answers a right-click with `TtlStory.talk`: the same lines as the Talk
//      button of an Easy NPC (`/ttl story talk <id>`). The entity's own right-click is cancelled (ItemEvents.entityInteracted),
//      except for a sneaking player (settings.sneak_bypass), so staff still reach Tensura's tame menu or a goblin's trade.
//      The game sends the click for both hands: only the main hand talks, both are cancelled, and a short cooldown
//      (settings.interact_cooldown_ms) swallows a double click.
// Staff and test commands (ops): /ttl cast list | load | unload | verify <spot|all> | interact <player> <spot|hook> <talk id> |
//   expect <field> <value>.   `load` force-loads the chunk of every placed spot (a chunk that is only loaded because a bot was
//   teleported there does not tick its entities), `unload` removes those tickets again, `verify` runs the check of a spot and
//   prints "ttl: ..." when it fails (a spot whose build is not placed is skipped), `interact` does what a right-click on that
//   spot's entity does, for a player, and checks the story id it talks with. tests/ingame/cast.rcon uses all of them.
const TtlCast = {
  TALK_TAG: 'ttl.talk.',
  // Tame (a dummy Owner no player has), mindless, unhurtable, silent, kept in the world; Phase 0 = the resting phase of the
  // entities that have one (Gazel, Hinata, Carrion, Luminous). Rotation, name and tags are added per statue.
  STATUE_NBT: 'NoAI:1b,Invulnerable:1b,Silent:1b,PersistenceRequired:1b,Phase:0,Owner:[I;0,0,0,1],CustomNameVisible:1b',
  lastTalk: {},
  forced: [],

  conf() {
    return TtlData.npcs
  },

  hooks() {
    return this.conf().hook || []
  },

  // ---- statues ----------------------------------------------------------------------------------------------

  statueNbt(spot, kind) {
    var name = JSON.stringify({ color: String(kind.name_color), text: String(kind.name) })
    var tags = [TtlGuildNpc.ANY, String(spot.tag), TtlGuildNpc.spotTag(spot), this.TALK_TAG + String(kind.talk)]
    return `{${this.STATUE_NBT},Rotation:[${Number(spot.yaw)}f,0f],CustomName:'${name}',Tags:${JSON.stringify(tags)}}`
  },

  // Summons the statue at pos ({dim, x, y, z}); true on success.
  spawnStatue(server, spot, kind, pos) {
    var cmd = `execute in ${pos.dim} run summon ${kind.statue} ${pos.x} ${pos.y} ${pos.z} ${this.statueNbt(spot, kind)}`
    if (!(TtlCmd.run(server, cmd) > 0)) {
      console.error(`[ttl] cast: summoning ${kind.statue} for ${spot.id} at ${pos.dim} ${pos.x} ${pos.y} ${pos.z} failed; is the entity id right and the chunk loaded?`)
      return false
    }
    return true
  },

  // ---- who talks for an entity ----------------------------------------------------------------------------------

  nameOf(entity) {
    try {
      var n = entity.getCustomName()
      return n ? String(n.getString()) : ''
    } catch (e) {
      return ''
    }
  },

  // The story npc id this entity answers with, or ''.
  talkOf(entity) {
    var tags = entity.getTags()
    var arr = tags.toArray()
    for (var i = 0; i < arr.length; i++) {
      var t = String(arr[i])
      if (t.indexOf(this.TALK_TAG) === 0) return t.substring(this.TALK_TAG.length)
    }
    var hooks = this.hooks()
    var name = null
    for (var j = 0; j < hooks.length; j++) {
      var h = hooks[j]
      if (!tags.contains(String(h.tag))) continue
      if (h.name) {
        if (name === null) name = this.nameOf(entity)
        if (name !== String(h.name)) continue
      }
      return String(h.talk)
    }
    return ''
  },

  // What a right-click does for this player: the story lines of the entity's character. Returns the story id talked with ('' when
  // the entity has no talk, or it was a repeated click inside the cooldown).
  interact(server, player, entity, force) {
    var id = this.talkOf(entity)
    if (!id) return ''
    var key = String(entity.uuid) + '|' + String(player.username)
    var now = Date.now()
    var cool = Number(this.conf().settings.interact_cooldown_ms)
    if (!force && this.lastTalk[key] && now - this.lastTalk[key] < cool) return id
    this.lastTalk[key] = now
    if (typeof TtlStory === 'undefined' || typeof TtlStory.talk !== 'function') {
      player.tell(Text.gray('The story is not loaded.'))
      return id
    }
    var err = TtlStory.talk(server, player, id)
    if (err) player.tell(Text.red(err))
    return id
  },

  // ---- finding ------------------------------------------------------------------------------------------------

  // Loaded entities of a dimension for which `fn(entity)` is true.
  scan(server, dim, fn) {
    var out = []
    var level = server.getLevel(dim)
    if (!level) return out
    level.getEntities().forEach(e => {
      if (e.isAlive() && fn(e)) out.push(e)
    })
    return out
  },

  hook(id) {
    var all = this.hooks()
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  // The loaded entities a hook listens to.
  hooked(server, h) {
    var self = this
    return this.scan(server, 'minecraft:overworld', e => e.getTags().contains(String(h.tag)) && (!h.name || self.nameOf(e) === String(h.name)))
  },

  // ---- checks (test hooks) ------------------------------------------------------------------------------------------

  // Force-loads the chunk of every placed spot; returns how many.
  load(server) {
    var n = 0
    var self = this
    TtlGuildNpc.spots().forEach(s => {
      if (!TtlGuildNpc.active(server, s)) return
      var pos = TtlGuildNpc.resolve(server, s)
      if (!pos) return
      var cx = Math.floor(pos.x)
      var cz = Math.floor(pos.z)
      if (TtlCmd.run(server, `execute in ${pos.dim} run forceload add ${cx} ${cz}`) > 0) {
        self.forced.push({ dim: pos.dim, x: cx, z: cz })
        n++
      }
    })
    return n
  },

  unload(server) {
    var n = this.forced.length
    this.forced.forEach(f => TtlCmd.run(server, `execute in ${f.dim} run forceload remove ${f.x} ${f.z}`))
    this.forced = []
    return n
  },

  // One spot: 'skipped (...)' when its anchor is not placed, else '' when everything holds, else the reason it does not.
  problem(server, spot) {
    var state = TtlGuildNpc.ensureSpot(server, spot)
    if (state === 'pending' || state === 'inactive') return `skipped (${state})`
    if (state === 'unloaded') return 'its chunk is not loaded (ttl cast load, wait a few seconds)'
    if (state === 'failed') return 'spawning failed (see the log)'
    var kind = TtlGuildNpc.kindOf(spot)
    var ents = TtlGuildNpc.find(server, String(spot.dim), TtlGuildNpc.spotTag(spot))
    if (ents.length !== 1) return `${ents.length} entities carry its tag, expected 1`
    var e = ents[0]
    var type = String(e.type)
    var want = kind.statue ? String(kind.statue) : null
    if (want ? type !== want : type.indexOf('easy_npc:') !== 0) {
      return 'is a ' + type + ', expected ' + (want || 'an Easy NPC')
    }
    if (!TtlGuildNpc.hasTag(e, String(spot.tag)) || !TtlGuildNpc.hasTag(e, TtlGuildNpc.ANY)) return 'lacks its ttl.npc tags'
    if (!e.isInvulnerable()) return 'is not invulnerable'
    if (kind.statue) {
      if (!TtlGuildNpc.hasTag(e, this.TALK_TAG + String(kind.talk))) return `lacks the tag ${this.TALK_TAG}${kind.talk}`
      var noai = true
      try {
        noai = !!e.isNoAi()
      } catch (x) {
        noai = true
      }
      if (!noai) return 'is not NoAI'
    }
    return ''
  },

  fact(server, field) {
    var self = this
    var all = {
      kinds: () => String(TtlGuildNpc.kinds().length),
      statue_kinds: () => String(TtlGuildNpc.kinds().filter(k => !!k.statue).length),
      talk_kinds: () => String(TtlGuildNpc.kinds().filter(k => !!k.talk).length),
      hooks: () => String(self.hooks().length),
      // every kind and hook talks with a story.toml [[npc]]
      talk_ids_known: () => String(TtlGuildNpc.kinds().filter(k => k.talk).every(k => !!TtlStory.npcDef(String(k.talk))) &&
        self.hooks().every(h => !!TtlStory.npcDef(String(h.talk))))
    }
    var m = /^hook_(.+)$/.exec(field)
    if (m) {
      var h = this.hook(m[1])
      if (!h) throw `unknown hook ${m[1]}`
      return String(this.hooked(server, h).length > 0 ? 'found' : 'none')
    }
    if (!(field in all)) throw `unknown field ${field} (one of ${Object.keys(all).join(', ')}, hook_<id>)`
    return all[field]()
  }
}

// The right-click. event.cancel() leaves the handler by throwing (KubeJS EventExit): it must stay outside any try/catch.
ItemEvents.entityInteracted(event => {
  var handled = false
  try {
    var target = event.target
    var player = event.entity
    if (target && player && TtlCast.talkOf(target)) {
      var sneak = false
      try {
        sneak = !!player.isCrouching()
      } catch (e) {
        sneak = false
      }
      if (!(sneak && TtlData.npcs.settings.sneak_bypass === true)) {
        handled = true
        if (String(event.hand) === 'MAIN_HAND') TtlCast.interact(player.getServer(), player, target, false)
      }
    }
  } catch (err) {
    console.error(`[ttl] cast: right-click handling failed: ${err}`)
  }
  if (handled) event.cancel()
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] cast command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var str = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var server = ctx => ctx.source.getServer()
  var ops = src => src.hasPermission(2)

  var list = ctx => {
    var s = server(ctx)
    TtlGuildNpc.spots().forEach(sp => {
      var k = TtlGuildNpc.kindOf(sp)
      say(ctx, `${sp.id}: ${k.statue ? 'statue ' + k.statue : 'Easy NPC'} talking ${k.talk || '(guild)'}, ${TtlGuildNpc.active(s, sp) ? 'active' : 'inactive'}, last check ${TtlGuildNpc.last[sp.id] || 'unchecked'}`)
    })
    TtlCast.hooks().forEach(h => say(ctx, `hook ${h.id}: tag ${h.tag}${h.name ? ' named ' + h.name : ''} -> ${h.talk}, ${TtlCast.hooked(s, h).length} loaded`))
    return 1
  }

  var load = ctx => {
    say(ctx, `cast: ${TtlCast.load(server(ctx))} chunks force-loaded`)
    return 1
  }

  var unload = ctx => {
    say(ctx, `cast: ${TtlCast.unload(server(ctx))} force-loaded chunks released`)
    return 1
  }

  var verify = ctx => {
    var s = server(ctx)
    var which = str(ctx, 'spot')
    var spots = which === 'all' ? TtlGuildNpc.spots() : [TtlGuildNpc.spot(which)]
    if (!spots[0]) throw `unknown spot ${which}`
    var bad = 0
    var skipped = 0
    var ok = 0
    spots.forEach(sp => {
      var why = TtlCast.problem(s, sp)
      if (why.indexOf('skipped') === 0) skipped++
      else if (why) {
        bad++
        ctx.source.sendSystemMessage(Text.red(`ttl: cast spot ${sp.id}: ${why}`))
      } else ok++
    })
    say(ctx, `cast verify ${which}: ${ok} ok, ${skipped} skipped (build not placed), ${bad} failed`)
    return bad === 0 ? 1 : 0
  }

  var interact = ctx => {
    var s = server(ctx)
    var p = Arguments.PLAYER.getResult(ctx, 'target')
    var what = str(ctx, 'what')
    var want = str(ctx, 'talk')
    var sp = TtlGuildNpc.spot(what)
    var h = sp ? null : TtlCast.hook(what)
    if (!sp && !h) throw `${what} is neither a spot nor a hook`
    var ents = sp ? TtlGuildNpc.find(s, String(sp.dim), TtlGuildNpc.spotTag(sp)) : TtlCast.hooked(s, h)
    if (ents.length === 0) {
      say(ctx, `cast interact ${what}: skipped (nothing loaded there)`)
      return 1
    }
    var kind = sp ? TtlGuildNpc.kindOf(sp) : null
    if (sp && !kind.statue) {
      // An Easy NPC answers through its dialog button, which runs this command: the check is the id the kind is wired to.
      if (String(kind.talk) !== want) throw `${what} talks with ${kind.talk}, expected ${want}`
      TtlStory.talk(s, p, want)
    } else {
      var got = TtlCast.interact(s, p, ents[0], true)
      if (got !== want) throw `${what} answers a right-click with ${got || 'nothing'}, expected ${want}`
    }
    say(ctx, `cast interact ${what}: ${p.username} talked with ${want}`)
    return 1
  }

  var expect = ctx => {
    var field = str(ctx, 'field')
    var want = str(ctx, 'value')
    var got = TtlCast.fact(server(ctx), field)
    if (got !== want) throw `expected cast ${field}=${want}, got ${got}`
    say(ctx, `cast ${field}=${want} as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('cast').requires(ops)
      .then(Commands.literal('list').executes(logged(list)))
      .then(Commands.literal('load').executes(logged(load)))
      .then(Commands.literal('unload').executes(logged(unload)))
      .then(Commands.literal('verify').then(Commands.argument('spot', Arguments.STRING.create(event)).executes(logged(verify))))
      .then(Commands.literal('interact').then(Commands.argument('target', Arguments.PLAYER.create(event))
        .then(Commands.argument('what', Arguments.STRING.create(event))
          .then(Commands.argument('talk', Arguments.STRING.create(event)).executes(logged(interact))))))
      .then(Commands.literal('expect').then(Commands.argument('field', Arguments.STRING.create(event))
        .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expect)))))))
})
