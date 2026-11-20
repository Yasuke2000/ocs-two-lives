// priority: 73
// Friendly quest NPCs stay alive (Yasuke 20/11/2026: killable NPCs are the enemies of world/enemies.js, never the quest and
// story cast). The guild NPCs, the story cast and statues, the adventurers and Tempest's named residents are Invulnerable,
// but vanilla's invulnerability lets every damage type in the tag minecraft:bypasses_invulnerability through, and Tensura
// puts its soul and severance skills there (tensura:severance, disintegration, death_wish, curse, soul_consumed,
// energy_drain, ... in tensura-neoforge-2.0.1.5.jar data/minecraft/tags/damage_type/bypasses_invulnerability.json): one
// Severance and Fuze or Benimaru was dead and a quest broken.
// So: the guild NPCs and the story cast and its statues (tag `ttl.npc`), the town adventurers (`ttl.adv`) and Tempest's
// Invulnerable residents (`ttl_tempest_resident`: the named ones) take no damage at all, except /kill (generic_kill) and the
// void (out_of_world), which staff, the tests and the respawn checks rely on. Vulnerable NPCs (escort clients, hired
// companions, unnamed residents, choice-scene actors, the enemies) are not touched: they may die, at a price
// (rep/guards.js, roads.toml enemies.slay). Easy NPC answers isInvulnerable() true for most of its NPCs, so a tag decides,
// not that flag (an escort client must still be able to fall to a monster).
// Test: `ttl npcprotect expect <entity tag> protected|open` and tests/ingame/enemies.rcon (a Severance hit by a soul).
const TtlNpcProtect = {
  // Damage types that always land: /kill and the void (msg ids of minecraft:generic_kill and minecraft:out_of_world).
  ALLOW: ['genericKill', 'outOfWorld', 'minecraft:generic_kill', 'minecraft:out_of_world'],
  // Always shielded; RESIDENT only while Invulnerable (the unnamed goblins stay killable, at a price).
  TAGS: ['ttl.npc', 'ttl.adv'],
  RESIDENT: 'ttl_tempest_resident',
  blocked: 0,
  warned: false,

  protectedEntity(e) {
    try {
      if (!e || e.isPlayer()) return false
      var tags = e.getTags()
      for (var i = 0; i < this.TAGS.length; i++) {
        if (tags.contains(this.TAGS[i])) return true
      }
      return tags.contains(this.RESIDENT) && !!e.isInvulnerable()
    } catch (x) {
      return false
    }
  },

  // The damage type's msg id ("genericKill") or registry id, whichever this KubeJS exposes.
  kindOf(source) {
    var tries = [
      () => source.getMsgId(),
      () => source.getType(),
      () => source.type().msgId(),
      () => source.typeHolder().unwrapKey().get().location()
    ]
    for (var i = 0; i < tries.length; i++) {
      try {
        var v = tries[i]()
        if (v !== null && v !== undefined && String(v)) return String(v)
      } catch (x) {
        // try the next accessor
      }
    }
    return ''
  },

  // True when this blow must not land.
  shield(event) {
    if (!this.protectedEntity(event.entity)) return false
    var id = this.kindOf(event.source)
    if (!id && !this.warned) {
      this.warned = true
      console.warn('[ttl] npc protect: cannot read the damage type of a blow; /kill on a protected NPC is blocked too')
    }
    if (this.ALLOW.indexOf(id) >= 0) return false
    this.blocked++
    return true
  }
}

EntityEvents.beforeHurt(event => {
  var stop = false
  try {
    stop = TtlNpcProtect.shield(event)
  } catch (e) {
    console.error(`[ttl] npc protect: hurt check failed: ${e}`)
  }
  // event.cancel() exits by throwing (KubeJS EventExit): never inside a try that catches it.
  if (stop) event.cancel()
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  event.register(Commands.literal('ttl')
    .then(Commands.literal('npcprotect').requires(src => src.hasPermission(2))
      .then(Commands.literal('expect').then(Commands.argument('tag', Arguments.STRING.create(event))
        .then(Commands.argument('state', Arguments.STRING.create(event)).executes(ctx => {
          var tag = String(Arguments.STRING.getResult(ctx, 'tag'))
          var want = String(Arguments.STRING.getResult(ctx, 'state'))
          var found = null
          ctx.source.getServer().getAllLevels().forEach(level => level.getEntities().forEach(e => {
            if (!found && e.isAlive() && e.getTags().contains(tag)) found = e
          }))
          if (!found) {
            ctx.source.sendSystemMessage(Text.red(`ttl: npc protect: no living entity tagged ${tag}`))
            return 0
          }
          var got = TtlNpcProtect.protectedEntity(found) ? 'protected' : 'open'
          if (got !== want) {
            ctx.source.sendSystemMessage(Text.red(`ttl: npc protect: ${tag} is ${got}, expected ${want}`))
            return 0
          }
          ctx.source.sendSystemMessage(Text.of(`npc protect: ${tag} ${got} as expected (${TtlNpcProtect.blocked} blow(s) stopped)`))
          return 1
        }))))))
})
