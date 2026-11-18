// priority: 87
// Karma v1, shown: the Voice of the World judges the life that just ended (TtlCorridor.begin), and the
// Life screen (a /ttlmenu chest screen; also /ttl life at any time) lists what the soul did, group by group
// (design/data/karma.toml [[groups]]), with the tier it earned.
const TtlKarmaView = {
  // "Hero", "Fallen Hero", ...
  title(v) {
    var conf = TtlData.karma
    var i = TtlKarma.tierIndex(v ? v.tier : conf.default_tier)
    var title = TtlKarma.tiers()[i < 0 ? 0 : i].title
    return v && v.dark ? `${conf.dark.prefix} ${title}` : title
  },

  verdict(player) {
    return `Your soul: ${this.title(TtlKarma.record(player))}`
  },

  plural(n, one, many) {
    return `${n} ${n === 1 ? one : many}`
  },

  format(s, n) {
    if (s.format === 'days') {
      var days = Math.floor(n / TtlData.karma.ticks_per_day)
      var minutes = Math.floor(n / 1200)
      return `${days} (${Math.floor(minutes / 60)}h ${minutes % 60}m active)`
    }
    if (s.format === 'blocks') return `${n} blocks`
    if (s.format === 'explored') return `${Math.round(n / TtlData.karma.explore.cell_value)} squares`
    if (s.format === 'visited') return n > 0 ? 'yes' : 'no'
    return `${n}`
  },

  // {group: ["Label: value", ...]}; stats sharing a label are added together, zeros are left out.
  lines(v) {
    var deeds = v.deeds || {}
    var conf = TtlData.karma
    var sums = {}
    var order = []
    TtlKarma.stats().forEach(s => {
      if (!s.group || !s.label) return
      var id = `${s.group}|${s.label}`
      if (!sums[id]) {
        sums[id] = { s: s, n: 0 }
        order.push(id)
      }
      sums[id].n += deeds[s.key] || 0
    })
    var out = {}
    var self = this
    order.forEach(id => {
      var e = sums[id]
      if (e.n <= 0) return
      ;(out[e.s.group] = out[e.s.group] || []).push(`${e.s.label}: ${self.format(e.s, e.n)}`)
    })
    if (v.kinds > 0) (out[conf.hostiles.group] = out[conf.hostiles.group] || []).push(`${conf.hostiles.label}: ${v.kinds}`)
    return out
  },

  // The Voice line after death: how long, how many, which bosses, and the verdict.
  judge(server, player) {
    var v = TtlKarma.record(player)
    var name = player.username
    if (!v) {
      TtlCorridor.say(server, name, 'sekai_ga_kimeru')
      return
    }
    var tier = TtlKarma.tiers()[TtlKarma.tierIndex(v.tier)]
    var deeds = v.deeds || {}
    var bosses = TtlKarma.stats().filter(s => s.major && deeds[s.key] > 0).map(s => s.label)
    var lived = v.days > 0 ? `Report. You lived ${this.plural(v.days, 'day', 'days')}` : 'Report. You lived less than a day'
    var kills = deeds.mob_kills || 0
    var text = kills > 0 ? `${lived} and slew ${this.plural(kills, 'creature', 'creatures')}` : lived
    if (bosses.length > 0) text += `${kills > 0 ? ', the' : ' and slew the'} ${bosses.join(' and the ')}${kills > 0 ? ' among them' : ''}`
    text += '.'
    if (v.dark) text += ' Innocent blood stains your soul.'
    text += ` The world judges you: ${this.title(v)}.`
    TtlCorridor.say(server, name, v.dark || TtlKarma.tierIndex(v.tier) === 0 ? 'kono_michi_wa_kewashii' : 'sekai_ga_kimeru')
    TtlCorridor.voice(server, name, text)
    if (tier && tier.announce) {
      server.runCommandSilent(`tellraw @a ${JSON.stringify([
        { text: '[Voice of the World] ', color: 'gold' },
        { text: `Notice. The soul of ${name} enters the Spirit Corridor, judged ${this.title(v)}.`, color: 'yellow' }
      ])}`)
      TtlDiscord.legend(server, name, this.title(v))
    }
  },

  // What a tier gives at rebirth (karma.toml), as lore lines.
  perks(t) {
    var w = t.weights || {}
    var out = [`Rebirth: ${t.offers} races to choose from`,
      t.unique_choices > 1 ? `Unique Skill: pick 1 of ${Math.min(3, t.unique_choices)}` : 'Unique Skill: fate draws it (a Trial lets you pick)']
    if ((w.rare || 1) !== (w.common || 1)) out.push(`Rare uniques ${(w.rare || 1) > (w.common || 1) ? 'favoured' : 'less likely'} (${w.rare || 1}:${w.common || 1})`)
    if (t.bonus_count > 0) out.push(`Bonus: ${this.plural(t.bonus_count, 'extra skill', 'extra skills')}`)
    return out
  },

  // Requirement lines for tier t, "have / need" with a mark when met.
  needs(v, t) {
    var row = (label, have, need) => `${have >= need ? '✔' : '✘'} ${label}: ${have} / ${need}`
    var out = [row('Karma', v.score, t.min_score || 0)]
    if (t.min_days) out.push(row('Days survived', v.days, t.min_days))
    if (t.min_bosses) out.push(row('Great foes slain', v.bosses, t.min_bosses))
    return out
  },

  // The Life screen. In the Corridor its centre button leads on to the current step (the Last Wish).
  showLife(server, player) {
    try {
      var v = TtlKarma.current(server, player)
      var conf = TtlData.karma
      var items = []
      var head = v
        ? [`Karma: ${v.score}${v.preview ? ' (so far)' : ''}`, `Days survived: ${v.days}`, `Great foes slain: ${v.bosses}`, '']
          .concat(TtlKarma.axes().map(a => `${TtlCorridor.title(a)}: ${v.axes[a]}`))
        : ['Your first life left no record.']
      var tierIdx = Math.max(0, TtlKarma.tierIndex(v ? v.tier : conf.default_tier))
      var tier = TtlKarma.tiers()[tierIdx]
      if (v && v.preview && !v.dark && v.axes.chaos > 0) head = head.concat([`(Dark from Chaos ${conf.dark.min_score})`])
      items.push({
        slot: 4, item: v && v.dark ? conf.dark.item : tier.item, name: `${v && v.preview ? 'So far' : 'Your soul'}: ${this.title(v)}`,
        color: v && v.dark ? '#AA3333' : '#FFD966', lore: head.concat([''], this.perks(tier))
      })
      // Life 1 only: what the next tier needs, so the player knows what to aim for before dying.
      var next = TtlKarma.tiers()[tierIdx + 1]
      if (v && v.preview) {
        items.push(next
          ? { slot: 22, item: next.item, name: `Next: ${next.title}`, color: '#55FFFF',
              lore: this.needs(v, next).concat([''], this.perks(next)) }
          : { slot: 22, item: 'minecraft:beacon', name: 'The highest tier', color: '#55FFFF', lore: ['Nothing more to earn. Live on.'] })
      }
      var lines = v ? this.lines(v) : {}
      var slots = [10, 11, 12, 14, 15, 16]
      conf.groups.forEach((g, i) => {
        if (i >= slots.length) return
        var list = lines[g.id] || []
        items.push({ slot: slots[i], item: g.item, name: g.title, color: '#C9A0FF', lore: list.length ? list : [g.empty] })
      })
      var corridor = TtlLife.phase(player) === 'corridor'
      if (corridor) {
        items.push({ slot: 22, item: 'minecraft:end_crystal', name: 'Make your last wish', color: '#FFD966',
          lore: ['The life is over.', 'What did your soul wish for?'], command: 'ttl menu' })
      }
      TtlCorridor.menu(server, player, v && v.preview ? 'Your life so far' : 'The life you lived', 3, items, null)
      if (corridor) {
        TtlCorridor.buttons(server, player.username, 'Your life has been judged.', [
          { label: 'Your life', command: '/ttl life', hover: 'What your first life earned' },
          { label: 'Last wish', command: '/ttl menu', hover: 'Go on to your Last Wish' }
        ])
      }
    } catch (e) {
      console.error(`[ttl] karma: life screen for ${player.username} failed: ${e}`)
      if (TtlLife.phase(player) === 'corridor') TtlCorridor.showStep(server, player)
    }
  }
}
