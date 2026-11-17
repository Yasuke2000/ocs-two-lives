// priority: 90
// Golden rule 1: every unique-skill grant or revoke goes through here.
// Phase 0: innate uniques from a wish pool, one holder per unique (mirrors Tensura's trulyUnique).
// Slots, rarities, absorption and the reconcile loop come in Phase 1.
const TtlRegistry = {
  // Legendary uniques are never innate (master plan §5); they are only won by absorption.
  LEGENDARY: [
    'tensura:predator', 'tensura:great_sage', 'tensura:creator',
    'tensura:envy', 'tensura:greed', 'tensura:lust', 'tensura:pride', 'tensura:sloth', 'tensura:wrath'
  ],

  held(server) {
    const raw = server.persistentData.getString('ttl.reg.held')
    return raw ? raw.split(',') : []
  },

  // Free uniques from `pool`: not Legendary, not held by anyone.
  available(server, pool) {
    const held = this.held(server)
    const legendary = this.LEGENDARY
    return pool.filter(id => legendary.indexOf(id) < 0 && held.indexOf(id) < 0)
  },

  // Up to n distinct free uniques from `pool`, in random order.
  draw(server, pool, n) {
    const free = this.available(server, pool)
    const out = []
    while (out.length < n && free.length > 0) {
      out.push(free.splice(Math.floor(Math.random() * free.length), 1)[0])
    }
    return out
  },

  grant(server, player, skill) {
    if (this.available(server, [skill]).length === 0) {
      console.warn(`[ttl] registry: refused ${skill} for ${player.username} (legendary or held)`)
      return false
    }
    server.runCommandSilent(`tensura edit ability grant ${player.username} ${skill}`)
    const held = this.held(server)
    held.push(skill)
    server.persistentData.putString('ttl.reg.held', held.join(','))
    player.persistentData.putString('ttl.uniques', skill)
    console.info(`[ttl] registry: innate ${skill} -> ${player.username}`)
    return true
  },

  revokeAll(server, player) {
    server.runCommandSilent(`tensura reset ${player.username} skill`)
    const mine = player.persistentData.getString('ttl.uniques')
    if (mine) {
      const held = this.held(server).filter(id => id !== mine)
      server.persistentData.putString('ttl.reg.held', held.join(','))
      player.persistentData.remove('ttl.uniques')
    }
    console.info(`[ttl] registry: revoked all skills of ${player.username}`)
  }
}
