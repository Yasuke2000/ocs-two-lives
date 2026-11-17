// priority: 100
// Shared Two Lives helpers. Server scripts share one scope (KubeJS forbids writing to `global` there).
// The life is tracked with stages (ttl.life1 / ttl.corridor / ttl.life2) because stages survive
// Life 2 deaths; offers live in persistentData.
const TtlLife = {
  MORTAL: 'ttl:mortal_realm',
  // Life 1's own Nether and End; the ttl-portals mod links their portals to the Mortal Realm only.
  MORTAL_DIMS: ['ttl:mortal_realm', 'ttl:mortal_nether', 'ttl:mortal_end'],
  CORRIDOR: 'ttl:spirit_corridor',
  OVERWORLD: 'minecraft:overworld',
  // Phase 0 offer pool (reincarnationRaces from Tensura's config). Karma tiers replace this in Phase 1.
  RACES: ['human', 'elf', 'dwarf', 'merfolk', 'beastfolk', 'harpy', 'goblin', 'lizardman', 'orc', 'wight', 'ghoul'],

  phase(player) {
    if (player.stages.has('ttl.life2')) return 'life2'
    if (player.stages.has('ttl.corridor')) return 'corridor'
    if (player.stages.has('ttl.life1')) return 'life1'
    return null
  },

  isMortal(dimension) {
    return this.MORTAL_DIMS.indexOf(String(dimension)) >= 0
  },

  dimensionOf(player) {
    return String(player.level.dimension)
  },

  toMortal(server, player) {
    server.runCommandSilent(`execute in ${this.MORTAL} run spreadplayers 0 0 0 48 false ${player.username}`)
  },

  toCorridor(server, player) {
    server.runCommandSilent(`execute in ${this.CORRIDOR} run tp ${player.username} 0.5 65 0.5 0 0`)
  },

  toOverworld(server, player) {
    let x = 0
    let z = 0
    try {
      const spawn = server.overworld().getSharedSpawnPos()
      x = spawn.getX()
      z = spawn.getZ()
    } catch (e) {
      console.warn(`[ttl] world spawn unreadable, using 0 0: ${e}`)
    }
    server.runCommandSilent(`execute in ${this.OVERWORLD} run spreadplayers ${x} ${z} 0 32 false ${player.username}`)
  },

  // Slime stays in every offer (master plan §3); two more are drawn from the pool. Read by TtlCorridor.
  rollOffers() {
    const pool = this.RACES.slice()
    const offers = ['slime']
    while (offers.length < 3 && pool.length > 0) {
      offers.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0])
    }
    return offers
  }
}
