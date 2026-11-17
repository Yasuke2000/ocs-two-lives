// priority: 90
// Golden rule 1: every unique-skill grant or revoke goes through here.
// Uniques may be shared up to a cap per rarity (design/data/skills.toml → TtlData.skills). Legendary
// uniques are never drawn for a rebirth; they are only granted on purpose (admin, Legendary tier,
// absorption), up to their cap. Tensura's trulyUnique is off for this.
// Holders live in server persistentData `ttl.reg.holders` as JSON {skill: [player, ...]}.
// Uniques gained outside the registry (the Great Sage scene's wishes, Tensura itself) are caught by
// reconcile(), which reads what players really hold through TtlManas.
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

  heldBy(holders, name) {
    return Object.keys(holders).filter(id => holders[id].indexOf(name) >= 0).sort()
  },

  // `ttl.uniques` mirrors the holder map for /ttl inspect and bug reports.
  remember(server, player) {
    player.persistentData.putString('ttl.uniques', this.heldBy(this.holders(server), player.username).join(','))
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
    this.remember(server, player)
    console.info(`[ttl] registry: ${skill} -> ${name} (${holders[skill].length}/${this.capOf(skill)})`)
    return true
  },

  // One skill only: `revoke <p> all` would also wipe race intrinsics and earned resistances.
  revoke(server, player, skill) {
    var name = player.username
    server.runCommandSilent(`quietly tensura edit ability revoke ${name} ${skill}`)
    var holders = this.holders(server)
    if (holders[skill]) {
      holders[skill] = holders[skill].filter(n => n !== name)
      if (holders[skill].length === 0) delete holders[skill]
      this.save(server, holders)
    }
    this.remember(server, player)
    console.info(`[ttl] registry: revoked ${skill} from ${name}`)
  },

  // Every unique of the player, recorded or really held. Not `tensura reset <p> skill`: that rerolls one.
  revokeAll(server, player) {
    var held = this.heldBy(this.holders(server), player.username)
    ;(TtlManas.uniques(player) || []).forEach(id => { if (held.indexOf(id) < 0) held.push(id) })
    held.forEach(id => this.revoke(server, player, id))
    player.persistentData.remove('ttl.uniques')
    console.info(`[ttl] registry: revoked all uniques of ${player.username} (${held.length})`)
  },

  // Brings the holder map in line with what the player really holds. A unique gained outside the registry
  // is recorded while its rarity has room; over the cap, or a Legendary nobody granted, it is taken back and
  // a free unique of the same rarity is given instead, so a Great Sage wish is never simply lost.
  reconcile(server, player) {
    var actual = TtlManas.uniques(player)
    if (actual === null) return
    var name = player.username
    var holders = this.holders(server)
    var recorded = this.heldBy(holders, name)
    var self = this
    var refused = []
    recorded.forEach(id => {
      if (actual.indexOf(id) >= 0) return
      holders[id] = holders[id].filter(n => n !== name)
      if (holders[id].length === 0) delete holders[id]
      console.info(`[ttl] registry: ${name} no longer holds ${id}`)
    })
    actual.forEach(id => {
      if (recorded.indexOf(id) >= 0) return
      var list = holders[id] || []
      if (self.rarityOf(id) === 'legendary' || list.length >= self.capOf(id)) {
        refused.push(id)
        return
      }
      holders[id] = list.concat([name])
      console.info(`[ttl] registry: recorded ${id} for ${name}, gained outside the registry (${holders[id].length}/${self.capOf(id)})`)
    })
    this.save(server, holders)
    refused.forEach(id => {
      var rarity = self.rarityOf(id)
      console.warn(`[ttl] registry: ${name} gained ${id} outside the registry over its cap (${rarity}); taking it back`)
      server.runCommandSilent(`quietly tensura edit ability revoke ${name} ${id}`)
      var pool = rarity === 'legendary' ? [] : TtlData.skills[rarity].skills.map(p => `tensura:${p}`)
      var instead = self.draw(server, pool, 1, name)
      if (instead.length > 0 && self.grant(server, player, instead[0])) {
        TtlCorridor.voice(server, name, `${TtlCorridor.title(id)} already has all the souls it can hold. ${TtlCorridor.title(instead[0])} answers your wish instead.`)
      } else {
        TtlCorridor.voice(server, name, `${TtlCorridor.title(id)} already has all the souls it can hold, and no other skill answers.`)
      }
    })
    this.remember(server, player)
  },

  // Admin: drop every record of `skill` (its holders left or were reset by hand).
  free(server, skill) {
    var holders = this.holders(server)
    delete holders[skill]
    this.save(server, holders)
  }
}

// Reconcile on login, and every five minutes for everyone online (catches skills from any source).
PlayerEvents.loggedIn(event => {
  var { player, server } = event
  server.scheduleInTicks(60, () => TtlRegistry.reconcile(server, player))
})

ServerEvents.loaded(event => {
  var server = event.server
  var loop = () => server.scheduleInTicks(6000, () => {
    server.getPlayerList().getPlayers().forEach(p => TtlRegistry.reconcile(server, p))
    loop()
  })
  loop()
})
