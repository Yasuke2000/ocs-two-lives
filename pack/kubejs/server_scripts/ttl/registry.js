// priority: 90
// Golden rule 1: every unique-skill grant or revoke goes through here.
// Uniques may be shared up to a cap per rarity (design/data/skills.toml → TtlData.skills). Legendary
// uniques are never drawn for a rebirth; they are only granted on purpose (admin, Legendary tier,
// absorption), up to their cap. Tensura's trulyUnique is off for this.
// Holders live in server persistentData `ttl.reg.holders` as JSON {skill: [player, ...]}.
// Phase 1 adds a reconcile loop for skills gained outside the registry (Tensura, Great Sage wishes).
const TtlRegistry = {
  rarityOf(skill) {
    var path = String(skill).replace(/^.*:/, '')
    var s = TtlData.skills
    if (s.legendary.skills.indexOf(path) >= 0) return 'legendary'
    if (s.rare.skills.indexOf(path) >= 0) return 'rare'
    return 'common'
  },

  capOf(skill) {
    return TtlData.skills.caps[this.rarityOf(skill)]
  },

  holders(server) {
    var raw = String(server.persistentData.getString('ttl.reg.holders'))
    return raw ? JSON.parse(raw) : {}
  },

  save(server, holders) {
    server.persistentData.putString('ttl.reg.holders', JSON.stringify(holders))
  },

  // Uniques from `pool` that `name` could receive now: under their cap and not already theirs.
  // Legendary only when `allowLegendary` (deliberate grants, never rebirth draws).
  available(server, pool, name, allowLegendary) {
    var holders = this.holders(server)
    var self = this
    return pool.filter(id => {
      if (!allowLegendary && self.rarityOf(id) === 'legendary') return false
      var list = holders[id] || []
      return list.indexOf(name) < 0 && list.length < self.capOf(id)
    })
  },

  // Up to n distinct grantable uniques from `pool`, in random order.
  draw(server, pool, n, name) {
    var free = this.available(server, pool, name)
    var out = []
    while (out.length < n && free.length > 0) {
      out.push(free.splice(Math.floor(Math.random() * free.length), 1)[0])
    }
    return out
  },

  grant(server, player, skill) {
    var name = player.username
    if (this.available(server, [skill], name, true).length === 0) {
      console.warn(`[ttl] registry: refused ${skill} for ${name} (${this.rarityOf(skill)}, cap ${this.capOf(skill)} reached or already held)`)
      return false
    }
    server.runCommandSilent(`quietly tensura edit ability grant ${name} ${skill}`)
    var holders = this.holders(server)
    holders[skill] = (holders[skill] || []).concat([name])
    this.save(server, holders)
    player.persistentData.putString('ttl.uniques', skill)
    console.info(`[ttl] registry: ${skill} -> ${name} (${holders[skill].length}/${this.capOf(skill)})`)
    return true
  },

  revokeAll(server, player) {
    var name = player.username
    // Not `tensura reset <p> skill`: that rerolls a new random unique.
    server.runCommandSilent(`quietly tensura edit ability revoke ${name} all`)
    var holders = this.holders(server)
    Object.keys(holders).forEach(id => {
      holders[id] = holders[id].filter(n => n !== name)
      if (holders[id].length === 0) delete holders[id]
    })
    this.save(server, holders)
    player.persistentData.remove('ttl.uniques')
    console.info(`[ttl] registry: revoked all skills of ${name}`)
  },

  // Admin: drop every record of `skill` (its holders left or were reset by hand).
  free(server, skill) {
    var holders = this.holders(server)
    delete holders[skill]
    this.save(server, holders)
  }
}
