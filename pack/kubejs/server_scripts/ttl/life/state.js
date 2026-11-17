// priority: 100
// Shared Two Lives helpers. The life is tracked with stages (ttl.life1 / ttl.corridor / ttl.life2)
// because stages survive Life 2 deaths; offers live in persistentData.
global.ttlLife = {
  MORTAL: 'ttl:mortal_realm',
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
    const spawn = server.overworld().getSharedSpawnPos()
    server.runCommandSilent(`execute in ${this.OVERWORLD} run spreadplayers ${spawn.getX()} ${spawn.getZ()} 0 32 false ${player.username}`)
  },

  // Slime stays in every offer (master plan §3); two more are drawn from the pool.
  rollOffers() {
    const pool = this.RACES.slice()
    const offers = ['slime']
    while (offers.length < 3 && pool.length > 0) {
      offers.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0])
    }
    return offers
  }
}
