// priority: 50
// Ambient adventurers: the guild halls, plazas and road camps of the canon continent are populated with Easy NPC
// adventurers (sidequests work package; [ambient], [[place]] and [[adventurer]] in design/data/sidequests.toml).
//
// Cheap by design:
//   - a place is only looked at when a player is within ambient.active_range of it and its chunk is loaded, and only on
//     the canon continent (TtlSidePlaces.onContinent, rule R11); nothing is spawned into unloaded chunks;
//   - one missing adventurer per check per place (the town fills over a minute), never more than the place's `cap`
//     (counted with an `execute if entity @e[tag=...]` selector around the place);
//   - the adventurers are persistent Easy NPCs (invulnerable, RANDOM_STROLL_AROUND_HOME round the home this script sets,
//     speech-bubble lines from the preset); when the chunk unloads they stay in it and count again on the next visit.
// Day and night: once a minute a sweep walks the overworld's loaded entities once: an adventurer of an old `rev` or an
// unknown place is removed, a place over its cap loses the extras, and when night begins (ambient.night_start) the
// ones of a place with an `inn` get the inn as their home (they walk there); at dawn their day home again.
// Entity tags: `ttl.adv`, `ttl.adv.p.<place>`, `ttl.adv.k.<kind>`, `ttl.adv.r<rev>`, `ttl.adv.night` (sent to the inn).
// Staff: /ttl adventurers list | populate [place] | sweep | clear [place] | expect <place> count <n> (commands.js)
const TtlAdventurers = {
  TAG: 'ttl.adv',
  sweeps: 0,
  last: {},

  conf() {
    return TtlData.sidequests.ambient
  },

  revTag() {
    return `${this.TAG}.r${this.conf().rev}`
  },

  kindOfEntity(e) {
    var tags = e.getTags().toArray()
    for (var i = 0; i < tags.length; i++) {
      var t = String(tags[i])
      if (t.startsWith(`${this.TAG}.k.`)) return t.slice(this.TAG.length + 3)
    }
    return ''
  },

  placeOfEntity(e) {
    var tags = e.getTags().toArray()
    for (var i = 0; i < tags.length; i++) {
      var t = String(tags[i])
      if (t.startsWith(`${this.TAG}.p.`)) return t.slice(this.TAG.length + 3)
    }
    return ''
  },

  isNight(server) {
    var c = this.conf()
    var t = Number(server.overworld().getDayTime()) % 24000
    return c.night_start <= c.night_end ? t >= c.night_start && t < c.night_end : t >= c.night_start || t < c.night_end
  },

  playerNear(server, pos, range) {
    var players = server.getPlayerList().getPlayers().toArray()
    for (var i = 0; i < players.length; i++) {
      if (TtlSidePlaces.near(players[i], pos, range)) return true
    }
    return false
  },

  count(server, place, pos) {
    return TtlCmd.run(server, `execute in ${pos.dim} if entity @e[tag=${this.TAG}.p.${place.id},x=${pos.x},y=${pos.y},z=${pos.z},distance=..96]`)
  },

  // A kind that is not at the place yet (one adventurer is one named person with one look), else any of them.
  pickKind(server, place, pos, kinds) {
    var free = []
    for (var i = 0; i < kinds.length; i++) {
      var k = String(kinds[i])
      var sel = `@e[tag=${this.TAG}.p.${place.id},tag=${this.TAG}.k.${k},x=${pos.x},y=${pos.y},z=${pos.z},distance=..96]`
      if (!(TtlCmd.run(server, `execute in ${pos.dim} if entity ${sel}`) > 0)) free.push(k)
    }
    var from = free.length ? free : kinds
    return String(from[Math.floor(Math.random() * from.length)])
  },

  // The home an adventurer of this place should have now: the inn at night (when the place has one), else the day spot.
  homeOf(server, place, night) {
    if (night && place.inn) return TtlSidePlaces.resolve(server, place, place.inn)
    return TtlSidePlaces.resolve(server, place)
  },

  setHome(server, e, pos) {
    TtlSideNpc.cmd(server, e, `navigation set home {npc} ${Math.floor(pos.x)} ${Math.floor(pos.y)} ${Math.floor(pos.z)}`)
  },

  // One place: 'off' | 'pending' | 'far' | 'outside' | 'unloaded' | 'full' | 'spawned <kind>' | 'failed'.
  populate(server, place) {
    if (!(Number(place.cap || 0) > 0)) return 'off'
    var flat = TtlSidePlaces.resolve(server, place, null, true)
    if (!flat) return 'pending'
    if (!TtlSidePlaces.onContinent(flat.x, flat.z)) return 'outside'
    if (!this.playerNear(server, flat, Number(this.conf().active_range))) return 'far'
    if (!TtlSidePlaces.isLoaded(server, flat.dim, flat.x, flat.z)) return 'unloaded'
    var pos = TtlSidePlaces.resolve(server, place)
    if (!pos) return 'unloaded'
    var have = this.count(server, place, pos)
    if (have >= Number(place.cap)) return 'full'
    var kinds = place.kinds || []
    if (kinds.length === 0) return 'off'
    var kind = this.pickKind(server, place, pos, kinds)
    var at = { dim: pos.dim, x: pos.x, y: pos.y, z: pos.z }
    var r = Number(place.radius || 0)
    if (pos.surface && r > 0) {
      at.x = Math.floor(pos.x + (Math.random() * 2 - 1) * r) + 0.5
      at.z = Math.floor(pos.z + (Math.random() * 2 - 1) * r) + 0.5
      var sy = TtlSidePlaces.surfaceY(server, pos.dim, at.x, at.z)
      if (sy === null) return 'unloaded'
      at.y = sy
    }
    var night = this.isNight(server)
    var tags = [this.TAG, `${this.TAG}.p.${place.id}`, `${this.TAG}.k.${kind}`, this.revTag()]
    var e = TtlSideNpc.spawn(server, at, `ttl_adv_${kind}`, tags)
    if (!e) return 'failed'
    var home = night && place.inn ? this.homeOf(server, place, true) : pos
    if (night && place.inn) e.addTag(`${this.TAG}.night`)
    this.setHome(server, e, home || pos)
    return `spawned ${kind}`
  },

  populateAll(server) {
    var self = this
    var out = []
    TtlSidePlaces.all().forEach(p => {
      var r = 'off'
      try {
        r = self.populate(server, p)
      } catch (e) {
        r = 'failed'
        console.error(`[ttl] adventurers: ${p.id} failed: ${e}`)
      }
      self.last[p.id] = r
      if (String(r).startsWith('spawned')) console.info(`[ttl] adventurers: ${p.id} ${r}`)
      out.push(`${p.id}: ${r}`)
    })
    return out
  },

  // One pass over the overworld's loaded entities: stale ones out, extras out, inn/day homes on a day-night change.
  sweep(server, force) {
    var night = this.isNight(server)
    var turned = force || this.wasNight === undefined || this.wasNight !== night
    this.wasNight = night
    var seen = {}
    var removed = 0
    var moved = 0
    var self = this
    var level = server.getLevel(TtlSidePlaces.OVERWORLD)
    var list = []
    level.getEntities().forEach(e => {
      if (e.isAlive() && TtlSideNpc.hasTag(e, self.TAG)) list.push(e)
    })
    list.forEach(e => {
      var place = TtlSidePlaces.get(self.placeOfEntity(e))
      if (!place || !TtlSideNpc.hasTag(e, self.revTag()) || !(Number(place.cap || 0) > 0)) {
        TtlSideNpc.remove(server, e)
        removed++
        return
      }
      seen[place.id] = (seen[place.id] || 0) + 1
      if (seen[place.id] > Number(place.cap)) {
        TtlSideNpc.remove(server, e)
        removed++
        return
      }
      if (!turned || !place.inn) return
      var atInn = TtlSideNpc.hasTag(e, `${self.TAG}.night`)
      if (atInn === night) return
      var home = self.homeOf(server, place, night)
      if (!home) return
      self.setHome(server, e, home)
      if (night) e.addTag(`${self.TAG}.night`)
      else e.removeTag(`${self.TAG}.night`)
      moved++
    })
    if (removed || moved) console.info(`[ttl] adventurers: sweep removed ${removed}, sent ${moved} ${night ? 'to the inn' : 'back to work'}`)
    return { found: list.length, removed: removed, moved: moved, night: night }
  },

  clear(server, placeId) {
    var n = 0
    var self = this
    var list = []
    server.getLevel(TtlSidePlaces.OVERWORLD).getEntities().forEach(e => {
      if (!e.isAlive() || !TtlSideNpc.hasTag(e, self.TAG)) return
      if (placeId && self.placeOfEntity(e) !== String(placeId)) return
      list.push(e)
    })
    list.forEach(e => {
      TtlSideNpc.remove(server, e)
      n++
    })
    return n
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var every = Math.max(100, Number(TtlAdventurers.conf().check_ticks))
  var loop = () => server.scheduleInTicks(every, () => {
    try {
      // `ttl adventurers hold <s>` (test hook): no ambient spawns until then, so a test counts only its own populate calls.
      var held = Number(server.persistentData.getLong('ttl.adventurers.hold')) > Date.now()
      if (TtlAdventurers.conf().enabled && !held) {
        TtlAdventurers.populateAll(server)
        TtlAdventurers.sweeps++
        // Once a minute at the default 200-tick check.
        if (TtlAdventurers.sweeps % 6 === 0) TtlAdventurers.sweep(server, false)
      }
    } catch (e) {
      console.error(`[ttl] adventurers: check failed: ${e}`)
    }
    loop()
  })
  server.scheduleInTicks(400, () => loop())
})
