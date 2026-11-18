// priority: 80
// The Spirit Corridor, step by step (persistentData `ttl.step`):
//   wish   → pick a Last Wish                         (/ttl wish <id>)
//   race   → pick a race, or face the Trial first     (/ttl choose <race>, /ttl trial)
//   trial  → Trial of the Soul running                (trial.js)
//   unique → trial passed: pick 1 of 3 uniques        (/ttl unique <skill>)
// Without a passed trial the unique is drawn at random from the wish's pool.
const TtlCorridor = {
  KEYS: ['ttl.step', 'ttl.wish', 'ttl.offers', 'ttl.race', 'ttl.uniqueOptions', 'ttl.trial.done', 'ttl.trial.passed',
    'ttl.raceSet', 'ttl.trial.token', 'ttl.trial.ready', 'ttl.trial.wave', 'ttl.trial.q', 'ttl.trial.correct', 'ttl.trial.strikes'],

  title(id) {
    var path = String(id).replace(/^.*:/, '')
    return path.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  },

  // The Great Sage addon's Voice of the World: on-screen overlay plus the recorded clip. The English line
  // is the addon's own subtitle for the clip (greatsage.voice.<clip>), so it follows the client language.
  // Clip names come from the addon jar (assets/greatsage/sounds/world/); the Japanese lines are ours.
  CLIPS: {
    hajimari: '始まります。', shibou_kakunin: '死亡を確認しました。', tamashii_hosoku: '魂を捕捉。損傷はありません。',
    saigo_no_negai: '最後の願い。', kakunin_shimashita: '確認しました。', shuzoku_sentaku: '種族を選択してください。',
    kono_michi_wa_kewashii: 'この道は険しい。', shounin: '……承認します', sekai_ga_kimeru: '世界が決めます。',
    kouho_teiji: '候補を提示します。', tensei_kanryou: '転生、完了しました。', me_o_akete: '目を開けて。'
  },

  say(server, name, clip) {
    var jp = JSON.stringify({ text: this.CLIPS[clip] || '' })
    var en = JSON.stringify({ translate: `greatsage.voice.${clip}` })
    server.runCommandSilent(`greatsage worldvoice ${name} ${clip} ${jp} ${en}`)
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

  // Splits text into tooltip lines of about `width` characters.
  wrap(text, width) {
    var lines = []
    var line = ''
    String(text).split(' ').forEach(word => {
      if (line && (line + ' ' + word).length > width) {
        lines.push(line)
        line = word
      } else {
        line = line ? `${line} ${word}` : word
      }
    })
    if (line) lines.push(line)
    return lines
  },

  // On-screen choice menu (ttl-portals /ttlmenu: a chest screen whose items are buttons). One short chat
  // line reopens it, in case the player closes the screen.
  menu(server, player, title, rows, items, reopenHint) {
    var spec = { title: title, rows: rows, items: items }
    server.runCommandSilent(`ttlmenu ${player.username} ${JSON.stringify(spec)}`)
    if (reopenHint) this.buttons(server, player.username, reopenHint, [{ label: 'Open', command: '/ttl menu', hover: 'Reopen the choices' }])
  },

  // Entry point from death.js.
  begin(server, player) {
    var data = player.persistentData
    this.KEYS.forEach(k => data.remove(k))
    data.putString('ttl.step', 'wish')
    data.putString('ttl.offers', TtlLife.rollOffers(player).join(','))
    var name = player.username
    this.say(server, name, 'shibou_kakunin')
    server.scheduleInTicks(50, () => this.say(server, name, 'tamashii_hosoku'))
    // Karma v1: the world judges the life that ended (karma/view.js), then asks for the last wish.
    server.scheduleInTicks(100, () => TtlKarmaView.judge(server, player))
    server.scheduleInTicks(150, () => this.say(server, name, 'saigo_no_negai'))
    // The Life screen opens once the death lines have played; its button leads on to the wish menu. On the
    // first death the short Corridor guide (guide.js) comes first and opens the Life screen when it is closed.
    server.scheduleInTicks(160, () => {
      if (String(data.getString('ttl.step')) !== 'wish') return
      if (!TtlGuide.once(server, player, 'corridor', 'ttl life')) TtlKarmaView.showLife(server, player)
    })
  },

  // A screen opened while the client is still loading the new dimension gets closed by the loading
  // screen, so menus wait two seconds after a teleport.
  showLater(server, player) {
    server.scheduleInTicks(40, () => this.showStep(server, player))
  },

  // Reopens whatever the current Corridor step needs (/ttl menu, login, after a trial).
  showStep(server, player) {
    var step = String(player.persistentData.getString('ttl.step'))
    if (step === 'wish') this.showWishes(server, player)
    if (step === 'race') this.showRaces(server, player)
    if (step === 'unique') this.showUniques(server, player)
    if (step === 'rebirth') this.startRebirth(server, player)
    if (step === 'trial' && player.persistentData.getString('ttl.wish') === 'knowledge') TtlTrials.DEFS.knowledge.showQuestion(server, player)
  },

  WISH_ICONS: {
    strength: 'minecraft:iron_sword', knowledge: 'minecraft:book', protection: 'minecraft:shield',
    hunger: 'minecraft:cooked_beef', freedom: 'minecraft:feather', creation: 'minecraft:crafting_table',
    vengeance: 'minecraft:redstone', deceit: 'minecraft:ender_eye', dominion: 'minecraft:golden_helmet',
    survival: 'minecraft:totem_of_undying'
  },
  RACE_ICONS: {
    slime: 'minecraft:slime_ball', human: 'minecraft:bread', elf: 'minecraft:oak_sapling', dwarf: 'minecraft:iron_pickaxe',
    merfolk: 'minecraft:prismarine_shard', beastfolk: 'minecraft:bone', harpy: 'minecraft:feather',
    goblin: 'minecraft:emerald', lizardman: 'minecraft:turtle_scute', orc: 'minecraft:porkchop',
    wight: 'minecraft:bone_block', ghoul: 'minecraft:rotten_flesh'
  },

  showWishes(server, player) {
    var slots = [2, 3, 4, 5, 6, 11, 12, 13, 14, 15]
    var icons = this.WISH_ICONS
    var self = this
    var items = TtlWishes.LIST.map((w, i) => {
      var trial = TtlTrials.DEFS[w.id]
      var skills = w.pool.map(id => self.title(id)).join(', ')
      return {
        slot: slots[i], item: icons[w.id] || 'minecraft:paper', name: w.label, color: '#FFD966',
        lore: [`"${w.wish}"`, ''].concat(self.wrap(`Skills: ${skills}`, 34))
          .concat(trial ? ['', `Trial: ${trial.title}`] : []),
        command: `ttl wish ${w.id}`
      }
    })
    this.menu(server, player, 'What did your soul wish for?', 3, items, 'Make your last wish.')
  },

  showRaces(server, player) {
    var data = player.persistentData
    var offers = String(data.getString('ttl.offers')).split(',')
    var icons = this.RACE_ICONS
    var slots = [11, 13, 15]
    var items = [{
      slot: 13, item: 'minecraft:end_crystal', name: 'Begin your reincarnation', color: '#C9A0FF',
      lore: [TtlKarmaView.verdict(player), 'The world offers you:'].concat(offers.map(r => `  ${this.title(r)}`)).concat(['', 'Choose your new body in the', 'reincarnation ceremony.']),
      command: 'ttl rebirth'
    }]
    var trial = TtlTrials.DEFS[String(data.getString('ttl.wish'))]
    var hint = 'Begin your reincarnation.'
    if (trial && !data.getBoolean('ttl.trial.done')) {
      items.push({
        slot: 22, item: 'minecraft:nether_star', name: `Face the ${trial.title}`, color: '#FF5555',
        lore: this.wrap(trial.intro, 34).concat([`${trial.limit} seconds.`, '', 'Win: choose your skill yourself.', 'Lose: fate chooses it.']),
        command: 'ttl trial'
      })
      hint = 'Begin your reincarnation, or face your Trial first.'
    }
    this.menu(server, player, 'Choose your new body', 3, items, hint)
  },

  showUniques(server, player) {
    var options = String(player.persistentData.getString('ttl.uniqueOptions')).split(',')
    var slots = [11, 13, 15]
    var items = options.map((s, i) => ({
      slot: slots[i], item: 'minecraft:enchanted_book', name: this.title(s), color: '#D98CFF',
      lore: ['Unique Skill'], command: `ttl unique ${String(s).replace(/^.*:/, '')}`
    }))
    this.menu(server, player, 'Choose your Unique Skill', 3, items, 'Choose your Unique Skill.')
  },

  wish(server, player, id) {
    var data = player.persistentData
    if (data.getString('ttl.step') !== 'wish') return 'You have already made your wish.'
    var wish = TtlWishes.get(id)
    if (!wish) return `Unknown wish: ${id}`
    data.putString('ttl.wish', wish.id)
    data.putString('ttl.step', 'race')
    this.say(server, player.username, 'kakunin_shimashita')
    server.scheduleInTicks(30, () => this.say(server, player.username, 'shuzoku_sentaku'))
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
    // A passed Trial gives 1 of 3; Karma v1 lets high tiers choose without it (TtlKarma.uniqueChoices).
    var picks = data.getBoolean('ttl.trial.passed') ? 3 : TtlKarma.uniqueChoices(player)
    if (picks > 1) {
      var options = TtlRegistry.draw(server, pool, picks, player.username, TtlKarma.drawWeights(player))
      if (options.length > 0) {
        data.putString('ttl.uniqueOptions', options.join(','))
        data.putString('ttl.step', 'unique')
        this.say(server, player.username, 'kouho_teiji')
        this.showUniques(server, player)
        return null
      }
    }
    var drawn = TtlRegistry.draw(server, pool, 1, player.username, TtlKarma.drawWeights(player))
    this.rebirth(server, player, drawn.length > 0 ? drawn[0] : null)
    return null
  },

  // Opens Tensura's reincarnation menu (the Great Sage addon plays its scene over it) showing only this
  // player's offers. ttl-portals calls `/ttl reborn` when a race is confirmed.
  startRebirth(server, player) {
    var data = player.persistentData
    var step = String(data.getString('ttl.step'))
    if (step !== 'race' && step !== 'rebirth') return 'You cannot be reborn right now.'
    data.putString('ttl.step', 'rebirth')
    server.runCommandSilent(`ttlrebirth open ${player.username} ${String(data.getString('ttl.offers'))}`)
    return null
  },

  reborn(server, player, raceId) {
    var data = player.persistentData
    if (TtlLife.phase(player) !== 'corridor' || String(data.getString('ttl.step')) !== 'rebirth') return 'not waiting for a rebirth'
    var race = String(raceId).replace(/^.*:/, '')
    data.putString('ttl.race', race)
    data.putBoolean('ttl.raceSet', true)
    var pool = TtlWishes.get(String(data.getString('ttl.wish'))).pool
    // A passed Trial gives 1 of 3; Karma v1 lets high tiers choose without it (TtlKarma.uniqueChoices).
    var picks = data.getBoolean('ttl.trial.passed') ? 3 : TtlKarma.uniqueChoices(player)
    if (picks > 1) {
      var options = TtlRegistry.draw(server, pool, picks, player.username, TtlKarma.drawWeights(player))
      if (options.length > 0) {
        data.putString('ttl.uniqueOptions', options.join(','))
        data.putString('ttl.step', 'unique')
        this.say(server, player.username, 'kouho_teiji')
        this.showUniques(server, player)
        return null
      }
    }
    var drawn = TtlRegistry.draw(server, pool, 1, player.username, TtlKarma.drawWeights(player))
    this.rebirth(server, player, drawn.length > 0 ? drawn[0] : null)
    return null
  },

  unique(server, player, path) {
    var data = player.persistentData
    if (data.getString('ttl.step') !== 'unique') return 'You have no skill to choose right now.'
    var options = data.getString('ttl.uniqueOptions').split(',')
    var skill = `tensura:${path}`
    if (options.indexOf(skill) < 0) return `Not one of your options: ${options.map(s => this.title(s)).join(', ')}`
    // The race is already set when the reincarnation menu chose it.
    this.rebirth(server, player, skill)
    return null
  },

  rebirth(server, player, skill) {
    var data = player.persistentData
    var name = player.username
    var race = data.getString('ttl.race')
    // Set by the reincarnation menu already when the rebirth went through the Great Sage scene.
    if (!data.getBoolean('ttl.raceSet')) server.runCommandSilent(`quietly tensura edit race ${name} set tensura:${race}`)
    // The Great Sage addon announces the granted skill itself (overlay + name clip).
    if (!(skill && TtlRegistry.grant(server, player, skill))) {
      // Every unique in the wish's pool is taken: reborn without one rather than breaking the cap.
      this.voice(server, name, 'Your wish echoes, but no free skill answers it. You are reborn without one.')
    }
    // Karma v1: a Legend's soul also carries a non-unique skill (karma.toml bonus_skills).
    TtlKarma.grantBonus(server, player)
    // Reputation (rep/rep.js): faction standing seeded from the race and the Life 1 karma just judged.
    try { if (typeof TtlRep !== 'undefined') TtlRep.seed(server, player, race) } catch (e) { console.error(`[ttl] ${name}: reputation seed failed: ${e}`) }
    server.runCommandSilent(`quietly clear ${name}`)
    // Carryover (life/mortal_banned.js): ttl:soulbound items and the Mortal Realm soul stash return with the new body.
    try {
      TtlStash.restore(server, player)
    } catch (e) {
      console.error(`[ttl] ${name}: carryover restore failed: ${e}`)
    }
    // Soul Gem with the Life 1 verdict, Remembered Enchantment (life/carryover.js).
    try { if (typeof TtlSoul !== 'undefined') TtlSoul.restore(server, player) } catch (e) { console.error(`[ttl] ${name}: soul restore failed: ${e}`) }
    player.stages.remove('ttl.corridor')
    player.stages.add('ttl.life2')
    this.KEYS.forEach(k => data.remove(k))
    data.remove('ttl.killer')
    server.runCommandSilent(`quietly gamemode survival ${name}`)
    TtlLife.toOverworld(server, player)
    this.say(server, name, 'tensei_kanryou')
    server.scheduleInTicks(60, () => this.say(server, name, 'me_o_akete'))
    // The first Life 2 opens with a short guide (guide.js); it waits on the client until the ceremony has closed.
    server.scheduleInTicks(120, () => TtlGuide.once(server, player, 'life2', ''))
    // The Great Sage scene grants its own wishes as the menu closes; record them (or take back what breaks a cap).
    server.scheduleInTicks(100, () => TtlRegistry.reconcile(server, player))
    server.runCommandSilent(`tellraw @a ${JSON.stringify([
      { text: '[Voice of the World] ', color: 'gold' },
      { text: `${name} has been reborn as a ${this.title(race)}.`, color: 'yellow' }
    ])}`)
    console.info(`[ttl] ${name} reborn as ${race} with ${skill || 'no unique'}`)
    TtlDiscord.reborn(server, name, this.title(race))
  }
}
