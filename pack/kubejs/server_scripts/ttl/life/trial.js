// priority: 85
// Trial of the Soul: an optional fight in the Corridor hall. Three waves within three minutes on loan
// gear; win and you choose your unique from 3 options of your wish, lose (or "die") and fate draws one.
// One trial at a time: the hall is shared. Waves are tracked by counting live tagged mobs every second:
// EntityEvents.death did not fire for mob deaths in testing (only for players), so no death hooks here.
const TtlTrial = {
  TAG: 'ttl_trial',
  TIME_LIMIT: 3600,
  WAVES: [
    [['minecraft:zombie', 3]],
    [['minecraft:skeleton', 2], ['minecraft:spider', 2]],
    [['minecraft:vindicator', 1, 'Echo of Your Last Breath'], ['minecraft:husk', 2]]
  ],
  SPAWNS: [[8, 65, 8], [-8, 65, 8], [8, 65, -8], [-8, 65, -8], [0, 65, 9]],

  run(server, cmd) {
    server.runCommandSilent(`execute in ${TtlLife.CORRIDOR} run ${cmd}`)
  },

  start(server, player) {
    var data = player.persistentData
    if (data.getString('ttl.step') !== 'race') return 'Make your wish first.'
    if (data.getBoolean('ttl.trial.done')) return 'Your soul has already been tested.'
    var busy = server.persistentData.getString('ttl.trial.player')
    if (busy) return `${busy} is facing the Trial right now. Wait for them to finish.`

    var name = player.username
    var token = String(Date.now())
    server.persistentData.putString('ttl.trial.player', name)
    server.persistentData.putString('ttl.trial.token', token)
    server.persistentData.putInt('ttl.trial.wave', -1)
    data.putString('ttl.step', 'trial')

    server.runCommandSilent(`clear ${name}`)
    server.runCommandSilent(`item replace entity ${name} weapon.mainhand with minecraft:iron_sword`)
    server.runCommandSilent(`item replace entity ${name} weapon.offhand with minecraft:shield`)
    server.runCommandSilent(`item replace entity ${name} armor.head with minecraft:iron_helmet`)
    server.runCommandSilent(`item replace entity ${name} armor.chest with minecraft:iron_chestplate`)
    server.runCommandSilent(`item replace entity ${name} armor.legs with minecraft:iron_leggings`)
    server.runCommandSilent(`item replace entity ${name} armor.feet with minecraft:iron_boots`)
    server.runCommandSilent(`give ${name} minecraft:cooked_beef 8`)
    player.setHealth(player.getMaxHealth())
    TtlLife.toCorridor(server, player)
    server.runCommandSilent(`title ${name} title {"text":"Trial of the Soul","color":"red"}`)
    server.runCommandSilent(`title ${name} subtitle {"text":"Three waves. Three minutes.","color":"gray"}`)
    console.info(`[ttl] ${name} started the Trial of the Soul`)

    server.scheduleInTicks(60, () => this.spawnWave(server, 0))
    this.watch(server, token)
    server.scheduleInTicks(this.TIME_LIMIT, () => {
      if (server.persistentData.getString('ttl.trial.token') === token) this.finish(server, name, false, 'Time ran out.')
    })
    return null
  },

  spawnWave(server, index) {
    var wave = this.WAVES[index]
    var count = 0
    var spot = 0
    wave.forEach(group => {
      for (var i = 0; i < group[1]; i++) {
        var pos = this.SPAWNS[spot++ % this.SPAWNS.length]
        var nbt = { Tags: [this.TAG], PersistenceRequired: true }
        if (group[2]) nbt.CustomName = JSON.stringify({ text: group[2], color: 'dark_red' })
        // JSON.stringify gives valid SNBT for this shape (strings and booleans only).
        this.run(server, `summon ${group[0]} ${pos[0]} ${pos[1]} ${pos[2]} ${JSON.stringify(nbt)}`)
        count++
      }
    })
    server.persistentData.putInt('ttl.trial.wave', index)
    console.info(`[ttl] trial ${server.persistentData.getString('ttl.trial.player')}: wave ${index + 1} (${count} mobs)`)
    var name = server.persistentData.getString('ttl.trial.player')
    server.runCommandSilent(`title ${name} actionbar {"text":"Wave ${index + 1} of ${this.WAVES.length}","color":"red"}`)
  },

  alive(server) {
    var count = 0
    var tag = this.TAG
    server.getLevel(TtlLife.CORRIDOR).getEntities().forEach(e => {
      if (e.isAlive() && e.getTags().contains(tag)) count++
    })
    return count
  },

  // Once a second while this trial (token) runs: when a wave is cleared, send the next or end it.
  watch(server, token) {
    server.scheduleInTicks(20, () => {
      if (server.persistentData.getString('ttl.trial.token') !== token) return
      var wave = server.persistentData.getInt('ttl.trial.wave')
      if (wave >= 0 && this.alive(server) === 0) {
        if (wave + 1 < this.WAVES.length) {
          this.spawnWave(server, wave + 1)
        } else {
          this.finish(server, server.persistentData.getString('ttl.trial.player'), true, 'Your soul has proven itself.')
          return
        }
      }
      this.watch(server, token)
    })
  },

  onPlayerDeath(server, player) {
    if (server.persistentData.getString('ttl.trial.player') === player.username) {
      this.finish(server, player.username, false, 'Your soul faltered.')
    }
  },

  finish(server, name, passed, why) {
    server.persistentData.remove('ttl.trial.player')
    server.persistentData.remove('ttl.trial.token')
    this.run(server, `kill @e[tag=${this.TAG},distance=0..]`)
    // Mob drops and loan gear must not be carried into Life 2.
    this.run(server, 'kill @e[type=minecraft:item,distance=0..]')
    var player = server.getPlayerList().getPlayerByName(name)
    console.info(`[ttl] ${name} ${passed ? 'passed' : 'failed'} the Trial of the Soul (${why})`)
    if (!player) return
    var data = player.persistentData
    data.putBoolean('ttl.trial.done', true)
    data.putBoolean('ttl.trial.passed', passed)
    data.putString('ttl.step', 'race')
    server.runCommandSilent(`clear ${name}`)
    player.setHealth(player.getMaxHealth())
    TtlLife.toCorridor(server, player)
    TtlCorridor.voice(server, name, passed ? `${why} You may choose your skill.` : `${why} Fate will choose your skill.`)
    TtlCorridor.showRaces(server, player)
  }
}

// A restart mid-trial must not leave the hall locked.
ServerEvents.loaded(event => {
  event.server.persistentData.remove('ttl.trial.player')
  event.server.persistentData.remove('ttl.trial.token')
})
