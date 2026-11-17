// priority: 80
// The Spirit Corridor, step by step (persistentData `ttl.step`):
//   wish   → pick a Last Wish                         (/ttl wish <id>)
//   race   → pick a race, or face the Trial first     (/ttl choose <race>, /ttl trial)
//   trial  → Trial of the Soul running                (trial.js)
//   unique → trial passed: pick 1 of 3 uniques        (/ttl unique <skill>)
// Without a passed trial the unique is drawn at random from the wish's pool.
const TtlCorridor = {
  KEYS: ['ttl.step', 'ttl.wish', 'ttl.offers', 'ttl.race', 'ttl.uniqueOptions', 'ttl.trial.done', 'ttl.trial.passed'],

  title(id) {
    var path = String(id).replace(/^.*:/, '')
    return path.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  },

  voice(server, name, text) {
    server.runCommandSilent(`tellraw ${name} ${JSON.stringify([{ text: '[Voice of the World] ', color: 'gold' }, { text: text, color: 'yellow' }])}`)
  },

  buttons(server, name, intro, items) {
    var line = [{ text: `[Voice of the World] ${intro} `, color: 'gold' }]
    items.forEach(item => line.push({
      text: `[${item.label}]`,
      color: item.color || 'aqua',
      clickEvent: { action: 'run_command', value: item.command },
      hoverEvent: { action: 'show_text', contents: item.hover || item.label }
    }, ' '))
    server.runCommandSilent(`tellraw ${name} ${JSON.stringify(line)}`)
  },

  // Entry point from death.js.
  begin(server, player) {
    var data = player.persistentData
    this.KEYS.forEach(k => data.remove(k))
    data.putString('ttl.step', 'wish')
    data.putString('ttl.offers', TtlLife.rollOffers().join(','))
    this.showWishes(server, player)
  },

  showWishes(server, player) {
    this.buttons(server, player.username, 'Your body is gone. What did your soul wish for, at the very end?',
      TtlWishes.LIST.map(w => ({ label: w.label, command: `/ttl wish ${w.id}`, hover: `"${w.wish}"` })))
  },

  showRaces(server, player) {
    var data = player.persistentData
    var offers = data.getString('ttl.offers').split(',')
    this.buttons(server, player.username, 'Choose the body you will be reborn in:',
      offers.map(r => ({ label: this.title(r), command: `/ttl choose ${r}`, hover: `Reincarnate as ${this.title(r)}` })))
    if (!data.getBoolean('ttl.trial.done')) {
      this.buttons(server, player.username, 'Or prove your soul first, and choose your skill yourself:',
        [{ label: 'Face the Trial of the Soul', color: 'red', command: '/ttl trial', hover: 'Three waves, three minutes. Fail and fate decides.' }])
    }
  },

  showUniques(server, player) {
    var options = player.persistentData.getString('ttl.uniqueOptions').split(',')
    this.buttons(server, player.username, 'Your soul has proven itself. Choose what it becomes:',
      options.map(s => ({ label: this.title(s), color: 'light_purple', command: `/ttl unique ${s.replace(/^.*:/, '')}`, hover: s })))
  },

  wish(server, player, id) {
    var data = player.persistentData
    if (data.getString('ttl.step') !== 'wish') return 'You have already made your wish.'
    var wish = TtlWishes.get(id)
    if (!wish) return `Unknown wish: ${id}`
    data.putString('ttl.wish', wish.id)
    data.putString('ttl.step', 'race')
    this.voice(server, player.username, `Confirmed. "${wish.wish}" Your wish has been heard.`)
    console.info(`[ttl] ${player.username} wished for ${wish.id}`)
    this.showRaces(server, player)
    return null
  },

  choose(server, player, race) {
    var data = player.persistentData
    if (data.getString('ttl.step') !== 'race') return 'You cannot choose a race right now.'
    var offers = data.getString('ttl.offers').split(',')
    if (offers.indexOf(race) < 0) return `Not one of your offers: ${offers.join(', ')}`
    data.putString('ttl.race', race)
    var pool = TtlWishes.get(data.getString('ttl.wish')).pool
    if (data.getBoolean('ttl.trial.passed')) {
      var options = TtlRegistry.draw(server, pool, 3)
      if (options.length > 0) {
        data.putString('ttl.uniqueOptions', options.join(','))
        data.putString('ttl.step', 'unique')
        this.showUniques(server, player)
        return null
      }
    }
    var drawn = TtlRegistry.draw(server, pool, 1)
    this.rebirth(server, player, drawn.length > 0 ? drawn[0] : null)
    return null
  },

  unique(server, player, path) {
    var data = player.persistentData
    if (data.getString('ttl.step') !== 'unique') return 'You have no skill to choose right now.'
    var options = data.getString('ttl.uniqueOptions').split(',')
    var skill = `tensura:${path}`
    if (options.indexOf(skill) < 0) return `Not one of your options: ${options.map(s => this.title(s)).join(', ')}`
    this.rebirth(server, player, skill)
    return null
  },

  rebirth(server, player, skill) {
    var data = player.persistentData
    var name = player.username
    var race = data.getString('ttl.race')
    server.runCommandSilent(`tensura edit race ${name} set tensura:${race}`)
    if (skill && TtlRegistry.grant(server, player, skill)) {
      this.voice(server, name, `Confirmed. Unique Skill [${this.title(skill)}] acquired.`)
    } else {
      // Every unique in the wish's pool is taken: reborn without one rather than breaking the cap.
      this.voice(server, name, 'Your wish echoes, but no free skill answers it. You are reborn without one.')
    }
    player.stages.remove('ttl.corridor')
    player.stages.add('ttl.life2')
    this.KEYS.forEach(k => data.remove(k))
    server.runCommandSilent(`gamemode survival ${name}`)
    TtlLife.toOverworld(server, player)
    server.runCommandSilent(`tellraw @a ${JSON.stringify([
      { text: '[Voice of the World] ', color: 'gold' },
      { text: `${name} has been reborn as a ${this.title(race)}.`, color: 'yellow' }
    ])}`)
    console.info(`[ttl] ${name} reborn as ${race} with ${skill || 'no unique'}`)
  }
}
