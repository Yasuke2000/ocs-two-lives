// priority: 70
// What a kill costs, and who the guards turn on (design/data/factions.toml; the API is in rep.js).
//
// Kill penalty: a Life 2 player who kills
//   - an NPC of a faction (entity tag from the faction's npc_tags, e.g. `/tag <npc> add ttl.npc.dwargon`, or a type
//     from its npc_types such as tensura:dwarf) loses kill_penalty.npc with that faction, wherever they stand;
//   - another Life 2 player on a faction's ground (the canon region of the victim's position) loses
//     kill_penalty.player with that faction.
// EntityEvents.death is unreliable for mob kills here (karma.js reads kill statistics instead). It is the only hook that
// knows WHO struck the NPC, so it is tried first; if it does not fire for an Easy NPC in your test, give the NPC's own
// on-death action the command `/ttl rep add <killer> <faction> -15` (ops command, runs as the server).
//
// Guards: an entity tagged `ttl.guard.<faction>` within `reach` blocks of a Life 2 player whose band with that faction
// is rules.guard_attack_at or worse is aimed at the player. Easy NPC guards need their own attack setup for the hit
// itself (their attack/dialog settings); this only gives them the target. Verify in game: Mob.setTarget on an Easy NPC.
const TtlRepGuards = {
  reach: 24,
  warned: false,

  tags(entity) {
    var out = []
    try {
      entity.tags.forEach(t => out.push(String(t)))
    } catch (e) {
      // an entity without readable tags simply has no faction
    }
    return out
  },

  // The faction a victim belongs to as an NPC, or null.
  npcFaction(victim) {
    var tags = this.tags(victim)
    var type = String(victim.type)
    var all = TtlRep.list()
    for (var i = 0; i < all.length; i++) {
      var tagged = (all[i].npc_tags || []).some(t => tags.indexOf(String(t)) >= 0)
      var typed = (all[i].npc_types || []).some(t => String(t) === type)
      if (tagged || typed) return all[i]
    }
    return null
  },

  onDeath(event) {
    var victim = event.entity
    var killer = null
    try {
      killer = event.source.actual
    } catch (e) {
      return
    }
    if (!killer || !killer.isPlayer() || killer === victim) return
    if (TtlLife.phase(killer) !== 'life2') return
    // R11: no kill penalty outside the canon continent.
    try { if (typeof TtlWorld !== 'undefined' && !TtlWorld.onContinent(TtlLife.dimensionOf(victim), victim.x, victim.z)) return } catch (e) { console.error(`[ttl] rep: continent test failed, the penalty applies: ${e}`) }
    var fac = null
    var points = 0
    var what = ''
    if (victim.isPlayer()) {
      if (TtlLife.phase(victim) !== 'life2' || TtlLife.dimensionOf(victim) !== TtlLife.OVERWORLD) return
      fac = TtlRep.factionAt(victim.x, victim.z)
      if (fac) points = Number(fac.kill_penalty.player)
      what = `player ${victim.username}`
    } else {
      fac = this.npcFaction(victim)
      if (fac) points = Number(fac.kill_penalty.npc)
      what = `NPC ${String(victim.type)}`
    }
    if (!fac || points <= 0) return
    var server = event.server
    var now = TtlRep.add(server, killer, String(fac.id), -points, `killed ${what}`)
    if (now !== null) killer.tell(Text.red(`The ${fac.title} will remember that: reputation -${points} (now ${now}).`))
  },

  // Aims the guards near one player; the loop below calls this every two seconds.
  pulse(server, player) {
    var all = TtlRep.list()
    var box = player.boundingBox.inflate(this.reach)
    var guards = player.level.getEntitiesWithin(box)
    var self = this
    guards.forEach(e => {
      if (e === player || e.isPlayer()) return
      var tags = self.tags(e)
      for (var i = 0; i < all.length; i++) {
        var id = String(all[i].id)
        if (tags.indexOf(`ttl.guard.${id}`) < 0) continue
        if (!TtlRep.guardsHostile(player, id)) return
        try {
          e.setTarget(player)
        } catch (err) {
          if (!self.warned) console.warn(`[ttl] rep: could not aim guard ${String(e.type)} at a player (${err}); guards are not enforced`)
          self.warned = true
        }
        return
      }
    })
  }
}

EntityEvents.death(event => {
  try {
    TtlRepGuards.onDeath(event)
  } catch (e) {
    console.error(`[ttl] rep: kill penalty failed: ${e}`)
  }
})

ServerEvents.loaded(event => {
  var server = event.server
  var loop = () => server.scheduleInTicks(40, () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        if (TtlLife.phase(p) === 'life2' && TtlLife.dimensionOf(p) === TtlLife.OVERWORLD) TtlRepGuards.pulse(server, p)
      } catch (e) {
        console.error(`[ttl] rep: guard pulse for ${p.username} failed: ${e}`)
      }
    })
    loop()
  })
  loop()
})
