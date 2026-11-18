// priority: 85
// Trial of the Soul runner. The trial is chosen by the player's Last Wish (TtlTrials in trial_defs.js).
// One player per arena at a time; different arenas run side by side. A watcher runs once a second while
// the trial's token is current: time limit, the trial's own tick, and the pass/fail result.
const TtlTrial = {
  TAG: 'ttl_trial',

  run(server, cmd) {
    server.runCommandSilent(`execute in ${TtlLife.CORRIDOR} run ${cmd}`)
  },

  lockKey(wish) {
    return `ttl.trial.lock.${wish}`
  },

  def(wish) {
    return TtlTrials.DEFS[wish]
  },

  // Arenas are structures (blueprints/trial_<wish>.py → ttl:trial_<wish>), rebuilt whenever ARENA_VERSION
  // changes. The box is cleared first: a structure leaves the blocks it does not list untouched.
  // Chunks are force-loaded only while building.
  buildArenas(server) {
    if (server.persistentData.getInt('ttl.arenas.version') === TtlTrials.ARENA_VERSION) return
    var self = this
    TtlTrials.ORDER.forEach(wish => {
      var o = TtlTrials.origin(wish)
      self.run(server, `forceload add ${o.x - 16} ${o.z - 16} ${o.x + 16} ${o.z + 16}`)
    })
    // forceload takes effect on the next tick; filling before that hits unloaded chunks.
    server.scheduleInTicks(40, () => {
      TtlTrials.ORDER.forEach(wish => {
        var d = self.def(wish)
        var o = TtlTrials.origin(wish)
        var fy = o.y + (d.floorY || 0)
        self.run(server, `fill ${o.x - 16} ${fy - 1} ${o.z - 16} ${o.x + 16} ${o.y + 16} ${o.z + 16} minecraft:air`)
        self.run(server, `place template ttl:trial_${wish} ${o.x - 16} ${fy} ${o.z - 16}`)
        self.run(server, `forceload remove ${o.x - 16} ${o.z - 16} ${o.x + 16} ${o.z + 16}`)
      })
      server.persistentData.putInt('ttl.arenas.version', TtlTrials.ARENA_VERSION)
      console.info(`[ttl] trial arenas built (version ${TtlTrials.ARENA_VERSION})`)
    })
  },

  context(server, player, wish, seconds) {
    var self = this
    return {
      server: server, player: player, name: player.username, o: TtlTrials.origin(wish), wish: wish, seconds: seconds,
      data: player.persistentData,
      run: cmd => self.run(server, cmd)
    }
  },

  start(server, player) {
    var data = player.persistentData
    if (data.getString('ttl.step') !== 'race') return 'Make your wish first.'
    if (data.getBoolean('ttl.trial.done')) return 'Your soul has already been tested.'
    var wish = String(data.getString('ttl.wish'))
    var d = this.def(wish)
    if (!d) return `No trial answers the wish "${wish}".`
    var busy = server.persistentData.getString(this.lockKey(wish))
    if (busy) return `${busy} is facing this trial right now. Wait for them to finish.`

    var name = player.username
    var token = String(Date.now())
    server.persistentData.putString(this.lockKey(wish), name)
    data.putString('ttl.trial.token', token)
    data.putBoolean('ttl.trial.ready', false)
    data.putString('ttl.step', 'trial')

    var o = TtlTrials.origin(wish)
    // Keep the arena loaded for the whole trial: mobs summoned into a chunk that is still loading vanish.
    this.run(server, `forceload add ${o.x - 16} ${o.z - 16} ${o.x + 16} ${o.z + 16}`)
    server.runCommandSilent(`quietly clear ${name}`)
    d.gear.forEach(g => server.runCommandSilent(`quietly give ${name} minecraft:${g}`))
    player.setHealth(player.getMaxHealth())
    this.run(server, `tp ${name} ${o.x + d.start[0] + 0.5} ${o.y + d.start[1]} ${o.z + d.start[2] + 0.5} 0 0`)
    server.runCommandSilent(`title ${name} title ${TtlTrials.named(d.title, 'red')}`)
    server.runCommandSilent(`title ${name} subtitle ${TtlTrials.named(d.intro, 'gray')}`)
    TtlCorridor.say(server, name, 'kono_michi_wa_kewashii')
    TtlCorridor.voice(server, name, `Notice. ${d.title}: ${d.intro} (${d.limit} seconds)`)
    console.info(`[ttl] ${name} started the ${d.title}`)

    // forceload takes effect on the next tick; give the chunks time before summoning into them.
    server.scheduleInTicks(40, () => {
      if (data.getString('ttl.trial.token') !== token) return
      try {
        if (d.setup) d.setup(this.context(server, player, wish, 0))
      } catch (e) {
        console.error(`[ttl] trial ${wish} setup failed for ${name}: ${e}`)
      }
      data.putBoolean('ttl.trial.ready', true)
    })
    this.watch(server, name, wish, token, 0)
    return null
  },

  watch(server, name, wish, token, seconds) {
    server.scheduleInTicks(20, () => {
      var player = server.getPlayerList().getPlayerByName(name)
      if (!player) {
        server.persistentData.remove(this.lockKey(wish))
        this.cleanup(server, wish)
        return
      }
      if (player.persistentData.getString('ttl.trial.token') !== token) return
      var d = this.def(wish)
      var elapsed = seconds + 1
      if (elapsed >= d.limit) {
        this.finish(server, player, wish, !!d.passOnTimeout, d.passOnTimeout ? 'You endured.' : 'Time ran out.')
        return
      }
      var result = null
      try {
        // Checks like "is the ward alive" are meaningless before setup has summoned anything.
        var ready = player.persistentData.getBoolean('ttl.trial.ready')
        result = ready && d.tick ? d.tick(this.context(server, player, wish, elapsed)) : null
      } catch (e) {
        console.error(`[ttl] trial ${wish} tick failed for ${name}: ${e}`)
      }
      if (result === 'pass') return this.finish(server, player, wish, true, 'Your soul has proven itself.')
      if (result === 'fail') return this.finish(server, player, wish, false, 'Your soul faltered.')
      if (elapsed % 30 === 0) server.runCommandSilent(`title ${name} actionbar {"text":"${d.limit - elapsed} seconds left","color":"gray"}`)
      this.watch(server, name, wish, token, elapsed)
    })
  },

  onPlayerDeath(server, player) {
    var data = player.persistentData
    if (data.getString('ttl.step') !== 'trial') return
    this.finish(server, player, String(data.getString('ttl.wish')), false, 'Your soul faltered.')
  },

  // Called by /ttl answer during the Trial of Knowledge.
  answer(server, player, word) {
    var data = player.persistentData
    if (data.getString('ttl.step') !== 'trial' || data.getString('ttl.wish') !== 'knowledge') return 'There is no question to answer.'
    return TtlTrials.DEFS.knowledge.answer(server, player, word)
  },

  // Empties the arena: trial mobs, drops, loan gear on the floor, anvils and fire. Releases the forceload.
  cleanup(server, wish) {
    var o = TtlTrials.origin(wish)
    var box = `x=${o.x - 17},y=${o.y - 10},z=${o.z - 17},dx=34,dy=30,dz=34`
    this.run(server, `kill @e[tag=${this.TAG},${box}]`)
    this.run(server, `kill @e[type=minecraft:item,${box}]`)
    this.run(server, `kill @e[type=minecraft:falling_block,${box}]`)
    ;['minecraft:anvil', 'minecraft:chipped_anvil', 'minecraft:damaged_anvil', 'minecraft:fire'].forEach(b =>
      this.run(server, `fill ${o.x - 15} ${o.y + 1} ${o.z - 15} ${o.x + 15} ${o.y + 6} ${o.z + 15} minecraft:air replace ${b}`))
    this.run(server, `forceload remove ${o.x - 16} ${o.z - 16} ${o.x + 16} ${o.z + 16}`)
  },

  finish(server, player, wish, passed, why) {
    var name = player.username
    var data = player.persistentData
    server.persistentData.remove(this.lockKey(wish))
    data.remove('ttl.trial.token')
    // Mob drops and loan gear must not be carried into Life 2; hazards must not outlive the trial.
    this.cleanup(server, wish)
    console.info(`[ttl] ${name} ${passed ? 'passed' : 'failed'} the ${this.def(wish).title} (${why})`)
    data.putBoolean('ttl.trial.done', true)
    data.putBoolean('ttl.trial.passed', passed)
    data.putString('ttl.step', 'race')
    server.runCommandSilent(`quietly clear ${name}`)
    server.runCommandSilent(`quietly effect clear ${name}`)
    player.setHealth(player.getMaxHealth())
    player.getFoodData().setFoodLevel(20)
    player.clearFire()
    TtlLife.toCorridor(server, player)
    TtlCorridor.say(server, name, passed ? 'shounin' : 'sekai_ga_kimeru')
    TtlCorridor.showLater(server, player)
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  // A restart mid-trial must not leave arenas locked; join.js fails the interrupted player's trial.
  TtlTrials.ORDER.forEach(wish => server.persistentData.remove(TtlTrial.lockKey(wish)))
  TtlTrial.buildArenas(server)
})
