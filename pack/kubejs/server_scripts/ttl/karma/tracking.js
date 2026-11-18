// Karma v1: creates the stat objectives and records what vanilla statistics don't (karma.js, karma.toml).
// Tracked values live in player persistentData and only move while the player is in Life 1:
//   ttl.l1.active ticks of ACTIVE play (a sample counts only if the player moved on foot, looked around or acted
//                 since the previous one; AFK and idling are not counted, see [activity])
//   ttl.l1.far    ground explored on foot in the Mortal Realm: new squares (ttl.l1.cells) x cell_value, with a
//                 daily cap (ttl.l1.cellDay / ttl.l1.cellsToday), see [explore]
//   ttl.l1.nether 1 once seen in the Mortal Nether · ttl.l1.end 1 once seen in the Mortal End
//   ttl.l1.adv    advancements with a display earned during Life 1 (recipe unlocks have none)
ServerEvents.loaded(event => {
  var server = event.server
  try {
    TtlKarma.ensure(server)
  } catch (e) {
    console.error(`[ttl] karma: creating the stat objectives failed: ${e}`)
  }
  var every = Math.max(1, TtlData.karma.track_seconds) * 20
  var loop = () => server.scheduleInTicks(every, () => {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        TtlKarmaTrack.sample(server, p)
      } catch (e) {
        console.error(`[ttl] karma: sampling ${p.username} failed: ${e}`)
      }
    })
    loop()
  })
  loop()
})

const TtlKarmaTrack = {
  // Per-player state between two samples, in memory only: {x, y, z, yaw, pitch, dim, acted}. A restart or logout
  // just means the next sample only takes a baseline.
  mem: {},

  uid(player) {
    return TtlLife.uuid(player).toLowerCase()
  },

  // Wayfarer's Rest (mortal_spawn.js stores "x y z"), or 0 0 before it has been placed. No longer used for scoring.
  home(server) {
    var spawn = String(server.persistentData.getString('ttl.mortal.spawn')).split(' ')
    return spawn.length === 3 ? { x: Number(spawn[0]), z: Number(spawn[2]) } : { x: 0, z: 0 }
  },

  // The player did something (break, place, use, chat): the next sample counts as active.
  mark(player) {
    if (!player) return
    var st = this.mem[this.uid(player)]
    if (st) st.acted = true
  },

  // Players already in Life 1 when active time was introduced carry their old play-time statistic over once.
  seedActive(server, player) {
    var data = player.persistentData
    var key = TtlKarma.TRACKED.active
    if (data.contains(key)) return
    var seed = 0
    try {
      var board = server.getScoreboard()
      var obj = board.getObjective(`${TtlKarma.OBJ}play_time`)
      var base = TtlKarma.base(player).play_time
      if (obj && base !== undefined) {
        var info = board.getPlayerScoreInfo(player, obj)
        seed = Math.max(0, (info ? info.value() : 0) - base)
      }
    } catch (e) {
      console.warn(`[ttl] karma: carrying over play time for ${player.username} failed: ${e}`)
    }
    data.putInt(key, seed)
    console.info(`[ttl] karma: ${player.username} starts counting active time at ${seed} ticks (carried over)`)
  },

  // Was the player active since the previous sample? Walking counts only on foot (a boat, mount, elytra or water
  // current moves an idle player); looking around or any action counts anywhere.
  isActive(player, st, now, dim) {
    var act = TtlData.karma.activity || { min_move: 1.5, min_turn: 15 }
    if (!st) return false
    if (st.acted) return true
    if (st.dim !== dim) return true
    var dyaw = Math.abs(now.yaw - st.yaw) % 360
    if (dyaw > 180) dyaw = 360 - dyaw
    if (dyaw >= act.min_turn || Math.abs(now.pitch - st.pitch) >= act.min_turn) return true
    var dx = now.x - st.x
    var dy = now.y - st.y
    var dz = now.z - st.z
    return Math.sqrt(dx * dx + dy * dy + dz * dz) >= act.min_move && !this.drifting(player)
  },

  // Rhino can't see every Entity method on a ServerPlayer (see TtlLife.uuid): each read has a fallback, and a read
  // that fails altogether counts as "not drifting" / no rotation rather than stopping the sample.
  read(label, primary, fallback, otherwise) {
    try {
      return primary()
    } catch (e) {
      try {
        return fallback()
      } catch (e2) {
        if (!this.warned[label]) {
          this.warned[label] = true
          console.warn(`[ttl] karma: cannot read ${label} of a player (${e2}); activity checks ignore it`)
        }
        return otherwise
      }
    }
  },
  warned: {},

  yaw(p) {
    return Number(this.read('yaw', () => p.getYRot(), () => p.yaw, 0))
  },

  pitch(p) {
    return Number(this.read('pitch', () => p.getXRot(), () => p.pitch, 0))
  },

  drifting(player) {
    var riding = this.read('vehicle', () => player.isPassenger(), () => !!player.vehicle, false)
    var wet = this.read('water', () => player.isInWater(), () => !!player.inWater, false)
    var gliding = this.read('gliding', () => player.isFallFlying(), () => !!player.fallFlying, false)
    return !!(riding || wet || gliding)
  },

  // One sample. `ticks` is the span it stands for (the sampling interval, or whatever a test passes).
  sample(server, player, ticks) {
    if (TtlLife.phase(player) !== 'life1') return
    var data = player.persistentData
    var keys = TtlKarma.TRACKED
    var dim = TtlLife.dimensionOf(player)
    if (dim === 'ttl:mortal_nether') data.putInt(keys.nether, 1)
    if (dim === 'ttl:mortal_end') data.putInt(keys.end, 1)
    this.seedActive(server, player)
    var id = this.uid(player)
    var st = this.mem[id]
    var now = { x: player.getX(), y: player.getY(), z: player.getZ(), yaw: this.yaw(player), pitch: this.pitch(player), dim: dim, acted: false }
    var active = this.isActive(player, st, now, dim)
    this.mem[id] = now
    if (!active) return
    data.putInt(keys.active, data.getInt(keys.active) + (ticks || Math.max(1, TtlData.karma.track_seconds) * 20))
    if (dim === TtlLife.MORTAL && !this.drifting(player)) this.visit(player, now.x, now.z)
  },

  // Credits the square around (x, z) once per Life 1, up to the daily cap. Returns true when it was new and counted.
  visit(player, x, z) {
    var ex = TtlData.karma.explore || { cell_size: 64, cell_value: 64, daily_cap: 30 }
    var data = player.persistentData
    var keys = TtlKarma.TRACKED
    var cell = `${Math.floor(x / ex.cell_size)}.${Math.floor(z / ex.cell_size)}`
    var seen = String(data.getString('ttl.l1.cells'))
    var list = seen ? seen.split(',') : []
    if (list.indexOf(cell) >= 0) return false
    var today = Math.floor(Date.now() / 86400000)
    if (data.getInt('ttl.l1.cellDay') !== today) {
      data.putInt('ttl.l1.cellDay', today)
      data.putInt('ttl.l1.cellsToday', 0)
    }
    var n = data.getInt('ttl.l1.cellsToday')
    if (n >= ex.daily_cap) return false
    data.putString('ttl.l1.cells', seen ? `${seen},${cell}` : cell)
    data.putInt('ttl.l1.cellsToday', n + 1)
    data.putInt(keys.far, data.getInt(keys.far) + ex.cell_value)
    return true
  },

  // Test hook: visit `n` squares in a row starting at (x, z); returns how many were counted.
  visitRow(player, x, z, n) {
    var size = (TtlData.karma.explore || { cell_size: 64 }).cell_size
    var counted = 0
    for (var i = 0; i < n; i++) {
      if (this.visit(player, x + i * size, z)) counted++
    }
    return counted
  }
}

// Idle time must not count: anything a player does between two samples marks them active. Wrapped one by one
// because an event name this KubeJS build lacks would otherwise stop the rest of this file from loading.
const ttlKarmaHook = (label, register) => {
  try {
    register(event => {
      try {
        TtlKarmaTrack.mark(event.player)
      } catch (e) { /* not a player (dispenser, piston): nothing to mark */ }
    })
  } catch (e) {
    console.warn(`[ttl] karma: cannot watch ${label} for activity: ${e}`)
  }
}
ttlKarmaHook('broken blocks', fn => BlockEvents.broken(fn))
ttlKarmaHook('placed blocks', fn => BlockEvents.placed(fn))
ttlKarmaHook('item use', fn => ItemEvents.rightClicked(fn))
ttlKarmaHook('chat', fn => PlayerEvents.chat(fn))
try {
  PlayerEvents.loggedOut(event => {
    delete TtlKarmaTrack.mem[TtlKarmaTrack.uid(event.player)]
  })
} catch (e) {
  console.warn(`[ttl] karma: cannot watch logouts for activity: ${e}`)
}

PlayerEvents.advancement(event => {
  var player = event.player
  if (TtlLife.phase(player) !== 'life1') return
  try {
    if (!event.advancement.hasDisplay()) return
  } catch (e) {
    return
  }
  var key = TtlKarma.TRACKED.advancements
  player.persistentData.putInt(key, player.persistentData.getInt(key) + 1)
})
