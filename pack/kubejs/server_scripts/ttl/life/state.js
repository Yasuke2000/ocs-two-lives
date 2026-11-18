// priority: 100
// Shared Two Lives helpers. Server scripts share one scope (KubeJS forbids writing to `global` there).
// Inside functions these scripts use `var`: Rhino throws "redeclaration of var" on block-scoped const/let.
// The life is tracked with stages (ttl.life1 / ttl.corridor / ttl.life2) because stages survive
// Life 2 deaths; offers live in persistentData.
const TtlLife = {
  MORTAL: 'ttl:mortal_realm',
  // Life 1's own Nether and End; the ttl-portals mod links their portals to the Mortal Realm only.
  MORTAL_DIMS: ['ttl:mortal_realm', 'ttl:mortal_nether', 'ttl:mortal_end'],
  CORRIDOR: 'ttl:spirit_corridor',
  OVERWORLD: 'minecraft:overworld',
  // Phase 0 offer pool (reincarnationRaces from Tensura's config). Karma v1 tiers replace it (karma/karma.js);
  // it stays as the fallback when karma fails.
  RACES: ['human', 'elf', 'dwarf', 'merfolk', 'beastfolk', 'harpy', 'goblin', 'lizardman', 'orc', 'wight', 'ghoul'],

  // The player's UUID as a string. Rhino can't see Entity.getUUID()/getStringUUID() on players here, so this goes
  // through KubeJS's own `uuid` property, then the game profile.
  uuid(player) {
    try {
      if (player.uuid) return String(player.uuid)
    } catch (e) {
      // fall through
    }
    return String(player.getGameProfile().getId())
  },

  phase(player) {
    if (player.stages.has('ttl.life2')) return 'life2'
    if (player.stages.has('ttl.corridor')) return 'corridor'
    if (player.stages.has('ttl.life1')) return 'life1'
    return null
  },

  // Life 1 is always Human. Setting it skips Tensura's one-option race menu (`tensura reset race` would
  // reopen that menu, which also keeps the player invulnerable until it is closed).
  makeHuman(server, player) {
    server.runCommandSilent(`quietly tensura edit race ${player.username} set tensura:human`)
  },

  isMortal(dimension) {
    return this.MORTAL_DIMS.indexOf(String(dimension)) >= 0
  },

  dimensionOf(player) {
    return String(player.level.dimension)
  },

  // Wayfarer's Rest (mortal_spawn.js), facing the shrine; spread around 0 0 until it has been placed.
  toMortal(server, player) {
    var spawn = String(server.persistentData.getString('ttl.mortal.spawn'))
    if (spawn) server.runCommandSilent(`execute in ${this.MORTAL} run tp ${player.username} ${spawn} 180 0`)
    else server.runCommandSilent(`execute in ${this.MORTAL} run spreadplayers 0 0 0 48 false ${player.username}`)
  },

  toCorridor(server, player) {
    server.runCommandSilent(`execute in ${this.CORRIDOR} run tp ${player.username} 0.5 65 0.5 0 0`)
  },

  // Life 2 begins on the safe rim of the Jura forest (life/arrival.js, design/data/arrival.toml), far from Tempest's
  // magicule-soaked core. Without a configured arrival: Tempest's green, facing its signpost (life/tempest.js stores
  // that point); before Tempest is placed, spread around the world spawn instead.
  toOverworld(server, player) {
    try {
      if (typeof TtlArrival !== 'undefined' && TtlArrival.send(server, player)) return
    } catch (e) {
      console.error(`[ttl] arrival teleport failed for ${player.username}, using Tempest's green: ${e}`)
    }
    var arrival = String(server.persistentData.getString('ttl.tempest.arrival'))
    if (arrival) {
      server.runCommandSilent(`execute in ${this.OVERWORLD} run tp ${player.username} ${arrival} 180 0`)
      return
    }
    var x = 0
    var z = 0
    try {
      var worldSpawn = server.overworld().getSharedSpawnPos()
      x = worldSpawn.getX()
      z = worldSpawn.getZ()
    } catch (e) {
      console.warn(`[ttl] world spawn unreadable, using 0 0: ${e}`)
    }
    server.runCommandSilent(`execute in ${this.OVERWORLD} run spreadplayers ${x} ${z} 0 32 false ${player.username}`)
  },

  // Slime stays in every offer (master plan §3); two more are drawn from the pool. Read by TtlCorridor.
  rollOffers(player) {
    // Karma v1: the Life 1 tier decides the pool and how many races are offered.
    if (player) {
      try {
        return TtlKarma.offers(player)
      } catch (e) {
        console.error(`[ttl] karma offers failed for ${player.username}, using the Phase 0 pool: ${e}`)
      }
    }
    var pool = this.RACES.slice()
    var offers = ['slime']
    while (offers.length < 3 && pool.length > 0) {
      offers.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0])
    }
    return offers
  }
}
