// A Wayfarer's Primer: a written book handed to every new Life 1 (once per life, a few seconds after joining, or
// by the 60 s milestone loop in whispers.js after a reset). It explains, in the world's own voice, what is judged
// at death and what each tier asks for; the tier page is built from TtlData.karma so it never drifts from
// design/data/karma.toml. Like everything carried in Life 1 it is lost at death.
// State: persistentData `ttl.l1.primer` = the ttl.l1.start of the life that got it.
const TtlPrimer = {
  KEY: 'ttl.l1.primer',
  TITLE: 'A Wayfarer\'s Primer',

  pages() {
    var karma = TtlData.karma
    var tiers = karma.tiers.map(t => {
      var needs = []
      if (t.min_score) needs.push(`${t.min_score} karma`)
      if (t.min_days) needs.push(`${t.min_days} days`)
      if (t.min_bosses) needs.push(`${t.min_bosses} great foe`)
      return `${t.title}: ${needs.length ? needs.join(', ') : 'any life'}`
    }).join('\n')
    // A book page shows ~14 short lines and never scrolls: keep each page under ~200 characters.
    return [
      'You are human, and here you live only once.\n\nWhen you die, your soul moves on to the Spirit Corridor. All you carry stays behind.\n\nWhat goes with you is what you did.',
      'THE JUDGEMENT\n\nThe Voice of the World weighs Valor, Order, Craft, Faith and Longevity, and one dark thing: Chaos.\n\nKarma decides the races and skills offered to your soul.',
      'VALOR\nMany kinds of foe (kinds count more than numbers), great foes, the Mortal Nether and End, roaming far.\n\nLONGEVITY\nEvery day alive. The first days count most.',
      'ORDER\nTrade with villagers, win their raids, tend animals.\n\nCHAOS\nSlay villagers, golems, traders or players, or bring a raid: your soul darkens and is reborn Fallen.',
      'CRAFT\nMine diamonds and ancient debris; work anvils and smithing tables.\n\nFAITH\nEnchant, brew and learn: every advancement counts.',
      `THE TIERS\n\n${tiers}\n\nYour best axis counts half again.`,
      'THE QUEST BOOK\n\nOpen it from your inventory. "A Mortal Life" lists the deeds of this realm and how each counts.\n\nLive well. Die meaningfully.'
    ]
  },

  // The give command: 1.21 written_book_content, each page a JSON text component inside an SNBT string.
  command(name) {
    var quote = s => `'${String(s).replace(/\\/g, '\\\\').replace(/'/g, '\\\'')}'`
    var pages = this.pages().map(p => quote(JSON.stringify({ text: p }))).join(',')
    return `give ${name} minecraft:written_book[minecraft:written_book_content={title:${quote(this.TITLE)},author:'Voice of the World',pages:[${pages}]}]`
  },

  life(player) {
    return String(player.persistentData.getLong('ttl.l1.start'))
  },

  // Gives the primer once per Life 1. Returns true when it gave one now.
  ensure(server, player) {
    if (TtlLife.phase(player) !== 'life1') return false
    var data = player.persistentData
    if (!data.contains('ttl.l1.start')) return false
    if (String(data.getString(this.KEY)) === this.life(player)) return false
    if (!TtlLife.isMortal(TtlLife.dimensionOf(player))) return false
    data.putString(this.KEY, this.life(player))
    server.runCommandSilent(this.command(player.username))
    return true
  }
}

PlayerEvents.loggedIn(event => {
  var { player, server } = event
  // join.js starts Life 1 and moves the player 20 ticks after login; give the book once they have landed.
  server.scheduleInTicks(100, () => {
    try {
      TtlPrimer.ensure(server, player)
    } catch (e) {
      console.error(`[ttl] quests: primer for ${player.username} failed: ${e}`)
    }
  })
})
