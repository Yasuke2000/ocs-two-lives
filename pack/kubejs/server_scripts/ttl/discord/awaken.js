// World events in #story: the awakenings the Great Sage addon announces in game through the Voice of the World
// (greatsage AwakeningWatcher: True Demon Lord, True Hero, Harvest Festival). It has no event for scripts,
// so this polls the same Tensura state it polls: TensuraStorages.getExistenceFrom(player) → isTrueDemonLord(),
// isTrueHero(), getHarvestTick() > 0. Seeds (Hero Egg, Demon Lord Seed) stay private, as in game.
// The last seen flags live in player persistentData `ttl.awaken`; a player's first sample only records, so a
// server restart or a new script never re-announces old awakenings. Naming has no state to poll (not relayed).
const TtlAwaken = {
  HARVEST: 1,
  HERO: 2,
  LORD: 4,
  api: undefined,

  load() {
    if (this.api !== undefined) return this.api
    try {
      this.api = Java.loadClass('io.github.manasmods.tensura.storage.TensuraStorages')
    } catch (e) {
      this.api = null
      console.info(`[ttl] awaken: Tensura existence storage not available, awakenings are not relayed (${e})`)
    }
    return this.api
  },

  flags(player) {
    var ex = this.load().getExistenceFrom(player)
    if (!ex) return null
    return (ex.getHarvestTick() > 0 ? this.HARVEST : 0) | (ex.isTrueHero() ? this.HERO : 0) | (ex.isTrueDemonLord() ? this.LORD : 0)
  },

  check(server, player) {
    var name = String(player.username)
    if (TtlDiscord.isBot(name)) return
    var now = this.flags(player)
    if (now === null) return
    var data = player.persistentData
    var seen = data.contains('ttl.awaken')
    var before = data.getInt('ttl.awaken')
    data.putInt('ttl.awaken', now)
    if (!seen) return
    var fresh = now & ~before
    var n = TtlDiscord.name(name)
    if (fresh & this.HARVEST) this.announce(server, name, 'Harvest Festival', `The Voice of the World: ${n} begins the evolution into a Demon Lord. **The Harvest Festival begins.**`)
    if (fresh & this.LORD) this.announce(server, name, 'True Demon Lord', `The Voice of the World: ${n} has awakened as a **True Demon Lord**.`)
    if (fresh & this.HERO) this.announce(server, name, 'True Hero', `The Voice of the World: ${n} has awakened as a **True Hero**.`)
  },

  announce(server, name, what, text) {
    console.info(`[ttl] awaken: ${name} ${what}`)
    TtlDiscord.post(server, text)
    TtlHall.noteAwakening(server, name, what)
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  if (!TtlAwaken.load()) return
  var loop = () => server.scheduleInTicks(Math.max(20, TtlData.discord.timing.awaken_ticks), () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        if (TtlLife.phase(p) === 'life2') TtlAwaken.check(server, p)
      } catch (e) {
        TtlSdlink.warn('awaken', e)
      }
    })
    loop()
  })
  loop()
})
