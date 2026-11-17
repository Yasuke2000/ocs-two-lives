// Life 1 milestone whispers: the Voice of the World speaks to a living mortal, privately and rarely, when a deed
// changes how their soul would be judged (first day, the Mortal Nether/End, a great foe, a darker soul, a higher
// tier, a week, a month). Death already gets its own lines (corridor_flow.js); this only covers the life itself.
// Calm by design: only the player hears it, at most one line per check (every 60 s), each line once per life.
// A life that already had deeds when this script first sees it (deploy, reset) is recorded silently, so nobody
// gets a backlog. State: persistentData `ttl.l1.whispers` = "<ttl.l1.start>|id,id,...".
// Ops/tests: /ttl quests tick <player> (check now), /ttl quests expect <player> said <id> (quests/check.js).
const TtlWhispers = {
  KEY: 'ttl.l1.whispers',
  EVERY: 1200,

  // In the order they are checked; `met(v)` gets the live karma preview (TtlKarma.current).
  MILESTONES: [
    { id: 'day1', met: v => v.days >= 1, text: () => 'One day and one night. The world takes note of those who endure.' },
    { id: 'nether', met: v => (v.deeds || {}).nether > 0, text: () => 'You walked the Mortal Nether and came back. Courage is remembered.' },
    { id: 'end', met: v => (v.deeds || {}).end > 0, text: () => 'You stand in the Mortal End. Few mortals come this far.' },
    { id: 'boss', met: v => v.bosses >= 1, text: () => 'A great foe has fallen by your hand. This deed will follow your soul.' },
    { id: 'dark', met: v => !!v.dark, text: () => 'Your hands are stained. If you died now, your soul would be reborn Fallen.' },
    { id: 'day7', met: v => v.days >= 7, text: () => 'Seven days. A soul that has lived this long may be judged a Hero.' },
    { id: 'day30', met: v => v.days >= 30, text: () => 'Thirty days. A full mortal life; the Legend tier is within your soul\'s reach.' }
  ],

  life(player) {
    return String(player.persistentData.getLong('ttl.l1.start'))
  },

  // The ids already said this life, or null when this life has no record yet.
  said(player) {
    var raw = String(player.persistentData.getString(this.KEY))
    var bar = raw.indexOf('|')
    if (bar < 0 || raw.substring(0, bar) !== this.life(player)) return null
    var rest = raw.substring(bar + 1)
    return rest ? rest.split(',') : []
  },

  store(player, ids) {
    player.persistentData.putString(this.KEY, `${this.life(player)}|${ids.join(',')}`)
  },

  // Every milestone this verdict has reached, tier milestones included ('tier.<id>' for each tier above the first).
  reached(v) {
    var ids = this.MILESTONES.filter(m => m.met(v)).map(m => m.id)
    var tiers = TtlKarma.tiers()
    var at = TtlKarma.tierIndex(v.tier)
    for (var i = 1; i <= at && i < tiers.length; i++) ids.push(`tier.${tiers[i].id}`)
    return ids
  },

  text(v, id) {
    if (id.indexOf('tier.') === 0) {
      var tier = TtlKarma.tiers()[TtlKarma.tierIndex(id.substring(5))]
      return `The world weighs your deeds. If your life ended now, your soul would be judged: ${tier.title}.`
    }
    var m = this.MILESTONES.filter(x => x.id === id)[0]
    return m ? m.text() : null
  },

  // Returns the id whispered, or ''.
  check(server, player) {
    if (TtlLife.phase(player) !== 'life1') return ''
    var v = TtlKarma.current(server, player)
    if (!v) return ''
    var reached = this.reached(v)
    var said = this.said(player)
    if (said === null) {
      this.store(player, reached)
      return ''
    }
    var next = reached.filter(id => said.indexOf(id) < 0)[0]
    if (!next) return ''
    said.push(next)
    this.store(player, said)
    var line = this.text(v, next)
    if (line) TtlCorridor.voice(server, player.username, line)
    return next
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var loop = () => server.scheduleInTicks(TtlWhispers.EVERY, () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        TtlPrimer.ensure(server, p)
        TtlWhispers.check(server, p)
      } catch (e) {
        console.error(`[ttl] quests: milestone check for ${p.username} failed: ${e}`)
      }
    })
    loop()
  })
  loop()
})
