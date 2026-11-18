// priority: 86
// The ten Trials of the Soul, one per Last Wish. Each lives in its own arena in the Spirit Corridor,
// 100 blocks apart along x, so different trials can run at the same time.
// Numbers (limit, gear, waves, questions, ...) live in design/data/trials.toml and are merged into each
// def at load (see the bottom of this file); intro(def) builds the start text from them.
// A trial: title + intro (shown at start), limit (seconds), passOnTimeout (survive-type trials),
// floorY (where the arena structure ttl:trial_<wish> is placed, see blueprints/trial_<wish>.py),
// start (player spawn, relative to the arena origin), gear (give arguments), setup(ctx) (mobs/items at start),
// tick(ctx) → 'pass' | 'fail' | null (each second).
// ctx: { server, player, name, o: origin {x,y,z}, data: player.persistentData, seconds, run(cmd), at(x,y,z) }.
// Checks only use accessors verified in KubeJS 2101 (position, food level, inventory count, isShiftKeyDown,
// entity tags/isAlive); mob deaths are counted, never hooked (EntityEvents.death skips mobs here).
const TtlTrials = {
  ORDER: ['strength', 'vengeance', 'protection', 'knowledge', 'hunger', 'freedom', 'deceit', 'creation', 'dominion', 'survival'],
  ARENA_VERSION: 3,

  origin(wish) {
    return { x: 1000 + 100 * this.ORDER.indexOf(wish), y: 64, z: 0 }
  },

  // Live tagged entities of this trial inside the arena box.
  count(ctx, tag) {
    var o = ctx.o
    var n = 0
    ctx.server.getLevel(TtlLife.CORRIDOR).getEntities().forEach(e => {
      if (!e.isAlive() || !e.getTags().contains(tag)) return
      if (Math.abs(e.getX() - o.x) <= 17 && Math.abs(e.getZ() - o.z) <= 17) n++
    })
    return n
  },

  mob(ctx, type, x, z, extra) {
    var nbt = { Tags: ['ttl_trial'], PersistenceRequired: true }
    if (extra) Object.keys(extra).forEach(k => { nbt[k] = extra[k] })
    // JSON.stringify gives valid SNBT for these shapes (strings, numbers, booleans, arrays, objects).
    ctx.run(`summon ${type} ${ctx.o.x + x} ${ctx.o.y + 1} ${ctx.o.z + z} ${JSON.stringify(nbt)}`)
  },

  item(ctx, id, count, x, z) {
    ctx.run(`summon minecraft:item ${ctx.o.x + x} ${ctx.o.y + 1.5} ${ctx.o.z + z} ${JSON.stringify({ Item: { id: id, count: count }, PickupDelay: 10, Tags: ['ttl_trial'] })}`)
  },

  named(text, color) {
    return JSON.stringify({ text: text, color: color || 'dark_red' })
  },

  DEFS: {
    strength: {
      title: 'Trial of Strength', start: [0, 1, -12],
      intro: d => `${d.waves.length} waves. Stand your ground.`,
      setup(ctx) {
        ctx.data.putInt('ttl.trial.wave', -1)
      },
      tick(ctx) {
        var wave = ctx.data.getInt('ttl.trial.wave')
        if (wave >= 0 && TtlTrials.count(ctx, 'ttl_trial') > 0) return null
        if (wave + 1 >= this.waves.length) return 'pass'
        var spots = [[10, 10], [-10, 10], [10, -2], [-10, -2], [0, 12]]
        var i = 0
        this.waves[wave + 1].forEach(group => {
          for (var k = 0; k < group[1]; k++) {
            var s = spots[i++ % spots.length]
            TtlTrials.mob(ctx, group[0], s[0], s[1], group[2] ? { CustomName: TtlTrials.named(group[2]) } : null)
          }
        })
        ctx.data.putInt('ttl.trial.wave', wave + 1)
        ctx.server.runCommandSilent(`title ${ctx.name} actionbar {"text":"Wave ${wave + 2} of ${this.waves.length}","color":"red"}`)
        console.info(`[ttl] trial ${ctx.name}: strength wave ${wave + 2}`)
        return null
      }
    },

    vengeance: {
      title: 'Trial of Vengeance', start: [0, 1, -12],
      intro: d => 'The one who killed you is here. Make it pay.',
      setup(ctx) {
        var killer = ctx.data.getString('ttl.killer')
        var type = this.duelists.indexOf(String(killer)) >= 0 ? String(killer) : this.fallback
        TtlTrials.mob(ctx, type, 0, 4, {
          CustomName: TtlTrials.named('The One Who Killed You'),
          attributes: [{ id: 'minecraft:generic.max_health', base: this.nemesis_health }],
          Health: this.nemesis_health,
          Tags: ['ttl_trial', 'ttl_nemesis']
        })
        console.info(`[ttl] trial ${ctx.name}: vengeance against ${type}`)
      },
      tick(ctx) {
        return ctx.seconds >= 2 && TtlTrials.count(ctx, 'ttl_nemesis') === 0 ? 'pass' : null
      }
    },

    protection: {
      title: 'Trial of Protection', passOnTimeout: true, start: [0, 1, -4],
      intro: d => `Keep them alive for ${d.limit} seconds.`,
      setup(ctx) {
        TtlTrials.mob(ctx, 'minecraft:villager', 0, 0, {
          NoAI: true,
          CustomName: TtlTrials.named('The One You Left Behind', 'green'),
          Tags: ['ttl_trial', 'ttl_ward']
        })
      },
      tick(ctx) {
        if (TtlTrials.count(ctx, 'ttl_ward') === 0) return 'fail'
        if (ctx.seconds % this.every === 1) {
          var corners = [[12, 12], [-12, 12], [12, -12], [-12, -12]]
          var n = this.raiders + Math.floor(ctx.seconds / 30)
          for (var i = 0; i < n; i++) {
            var c = corners[(i + ctx.seconds) % 4]
            TtlTrials.mob(ctx, i % 3 === 2 ? this.heavy : this.raider, c[0], c[1])
          }
        }
        return null
      }
    },

    knowledge: {
      title: 'Trial of Knowledge', start: [0, 1, 0],
      intro: d => `Answer the Voice. ${d.pass_score} of ${d.questions.length} must be right.`,
      setup(ctx) {
        ctx.data.putInt('ttl.trial.q', 0)
        ctx.data.putInt('ttl.trial.correct', 0)
        this.showQuestion(ctx.server, ctx.player)
      },
      // The question is the menu title (short) and the tooltip of every answer (full text).
      showQuestion(server, player) {
        var i = player.persistentData.getInt('ttl.trial.q')
        if (i >= this.questions.length) return
        var question = this.questions[i]
        TtlCorridor.voice(server, player.username, `Question ${i + 1} of ${this.questions.length}: ${question.q}`)
        var slots = [11, 13, 15]
        var lore = TtlCorridor.wrap(question.q, 34)
        TtlCorridor.menu(server, player, `Question ${i + 1} of ${this.questions.length}`, 3, question.options.map((o, k) => ({
          slot: slots[k], item: 'minecraft:paper', name: TtlCorridor.title(o), color: '#FFFFFF', lore: lore, command: `ttl answer ${o}`
        })), 'Answer the Voice.')
      },
      // Called by /ttl answer. Returns an error message or null.
      answer(server, player, word) {
        var data = player.persistentData
        var i = data.getInt('ttl.trial.q')
        if (i >= this.questions.length) return 'No question is waiting.'
        if (word === this.questions[i].a) data.putInt('ttl.trial.correct', data.getInt('ttl.trial.correct') + 1)
        data.putInt('ttl.trial.q', i + 1)
        if (i + 1 < this.questions.length) this.showQuestion(server, player)
        return null
      },
      tick(ctx) {
        if (ctx.data.getInt('ttl.trial.q') < this.questions.length) return null
        return ctx.data.getInt('ttl.trial.correct') >= this.pass_score ? 'pass' : 'fail'
      }
    },

    hunger: {
      title: 'Trial of Hunger', start: [0, 1, 0],
      intro: d => 'You are starving. Eat until you are full before time runs out.',
      setup(ctx) {
        ctx.player.getFoodData().setFoodLevel(this.start_food)
        var food = [['minecraft:bread', 1, 10, 10], ['minecraft:bread', 1, -10, 10], ['minecraft:bread', 1, 0, -12],
          ['minecraft:apple', 1, 12, -6], ['minecraft:apple', 1, -12, -6], ['minecraft:cooked_porkchop', 1, 6, 13],
          ['minecraft:cooked_porkchop', 1, -6, -13], ['minecraft:carrot', 2, 13, 0], ['minecraft:carrot', 2, -13, 0]]
        food.forEach(f => TtlTrials.item(ctx, f[0], f[1], f[2], f[3]))
        var spots = [[8, 8], [-8, -8], [8, -8], [-8, 8]]
        for (var i = 0; i < this.husks; i++) TtlTrials.mob(ctx, 'minecraft:husk', spots[i % 4][0], spots[i % 4][1])
      },
      tick(ctx) {
        return ctx.player.getFoodData().getFoodLevel() >= 20 ? 'pass' : null
      }
    },

    freedom: {
      title: 'Trial of Freedom', floorY: -6, start: [0, 1, -13],
      intro: d => 'Reach the golden platform. Fall, and you start over.',
      // The jump course over the pit is in blueprints/trial_freedom.py (COURSE).
      tick(ctx) {
        var p = ctx.player
        var dz = p.getZ() - ctx.o.z
        if (dz >= 11.5 && Math.abs(p.getX() - ctx.o.x) <= 2.5 && p.getY() >= ctx.o.y) return 'pass'
        if (p.getY() < ctx.o.y - 2) {
          ctx.server.runCommandSilent(`execute in ${TtlLife.CORRIDOR} run tp ${ctx.name} ${ctx.o.x + 0.5} ${ctx.o.y + 1} ${ctx.o.z - 12.5} 0 0`)
          ctx.server.runCommandSilent(`title ${ctx.name} actionbar {"text":"You fell. Again.","color":"gray"}`)
        }
        return null
      }
    },

    deceit: {
      title: 'Trial of Deceit', start: [0, 1, -14],
      intro: d => 'Reach the emerald exit unseen. Watchers see anyone who walks upright near them: sneak.',
      // Watcher rows (z): the start (z -14) is out of sight of the first row, the exit is checked first.
      ROWS: [-4, 3, 10],
      setup(ctx) {
        ctx.data.putInt('ttl.trial.strikes', 0)
        this.ROWS.forEach(z => [-8, 0, 8].forEach(x => TtlTrials.mob(ctx, 'minecraft:evoker', x, z, {
          NoAI: true, Invulnerable: true, Silent: true,
          CustomName: TtlTrials.named('Watcher', 'gray'), Tags: ['ttl_trial', 'ttl_watcher']
        })))
      },
      tick(ctx) {
        var p = ctx.player
        var dx = p.getX() - ctx.o.x
        var dz = p.getZ() - ctx.o.z
        if (dz >= 12.5 && Math.abs(dx) <= 2.5) return 'pass'
        if (p.isShiftKeyDown()) return null
        var seen = false
        var r = this.radius
        this.ROWS.forEach(wz => [-8, 0, 8].forEach(wx => {
          if (Math.sqrt((dx - wx) * (dx - wx) + (dz - wz) * (dz - wz)) <= r) seen = true
        }))
        if (!seen) return null
        var strikes = ctx.data.getInt('ttl.trial.strikes') + 1
        ctx.data.putInt('ttl.trial.strikes', strikes)
        if (strikes >= this.strikes) return 'fail'
        ctx.server.runCommandSilent(`execute in ${TtlLife.CORRIDOR} run tp ${ctx.name} ${ctx.o.x + 0.5} ${ctx.o.y + 1} ${ctx.o.z - 13.5} 0 0`)
        ctx.server.runCommandSilent(`title ${ctx.name} actionbar {"text":"Seen! ${this.strikes - strikes} chance(s) left. Sneak.","color":"red"}`)
        return null
      }
    },

    creation: {
      title: 'Trial of Creation', start: [0, 1, -6],
      // Not TtlCorridor.title: corridor_flow.js loads after this file.
      intro: d => `Gather what lies around you and craft a ${String(d.target).replace(/^.*:/, '').replace(/_/g, ' ')}.`,
      setup(ctx) {
        var parts = [['minecraft:iron_ingot', 1, 12, 12], ['minecraft:coal', 1, -12, 10], ['minecraft:stick', 1, 10, -12],
          ['minecraft:cobblestone', 4, -10, -12], ['minecraft:string', 2, 13, 0], ['minecraft:flint', 1, -13, 0]]
        parts.forEach(i => TtlTrials.item(ctx, i[0], i[1], i[2], i[3]))
      },
      tick(ctx) {
        return ctx.player.inventory.count(this.target) > 0 ? 'pass' : null
      }
    },

    dominion: {
      title: 'Trial of Dominion', start: [0, 1, 0],
      intro: d => `Bring ${d.needed} of the herd into the pen.`,
      PEN: { x1: 9, z1: 9, x2: 13, z2: 13 },
      setup(ctx) {
        var spots = [[-10, -10], [-12, -6], [-6, -12], [-12, -12], [-8, -8], [-4, -10], [-10, -4], [-6, -6]]
        for (var i = 0; i < this.herd; i++) {
          var c = spots[i % spots.length]
          TtlTrials.mob(ctx, 'minecraft:cow', c[0], c[1], { Tags: ['ttl_trial', 'ttl_herd'] })
        }
      },
      tick(ctx) {
        var pen = this.PEN
        var o = ctx.o
        var inside = 0
        ctx.server.getLevel(TtlLife.CORRIDOR).getEntities().forEach(e => {
          if (!e.isAlive() || !e.getTags().contains('ttl_herd')) return
          var x = e.getX() - o.x
          var z = e.getZ() - o.z
          if (x >= pen.x1 && x <= pen.x2 + 1 && z >= pen.z1 && z <= pen.z2 + 1) inside++
        })
        return inside >= this.needed ? 'pass' : null
      }
    },

    survival: {
      title: 'Trial of Survival', passOnTimeout: true, start: [0, 1, 0],
      intro: d => `No weapons. Live for ${d.limit} seconds.`,
      setup(ctx) {
        var spots = [[12, 12], [-12, -12], [12, -12], [-12, 12]]
        for (var i = 0; i < this.skeletons; i++) TtlTrials.mob(ctx, 'minecraft:skeleton', spots[i % 4][0], spots[i % 4][1])
      },
      tick(ctx) {
        var every = this.hazard_every
        if (ctx.seconds % every !== Math.floor(every / 2)) return null
        var n = ctx.name
        var hazard = Math.floor(ctx.seconds / every) % 3
        if (hazard === 0) ctx.server.runCommandSilent(`quietly effect give ${n} minecraft:poison 5 0`)
        if (hazard === 1) ctx.run(`execute at ${n} run summon minecraft:falling_block ~ ~9 ~ {BlockState:{Name:"minecraft:anvil"},Time:1,DropItem:0b,HurtEntities:1b,FallHurtMax:6,FallHurtAmount:1.0f}`)
        if (hazard === 2) ctx.run(`execute at ${n} run setblock ~ ~ ~ minecraft:fire`)
        return null
      }
    }
  }
}

// design/data/trials.toml → TtlData.trials: each trial's knobs become fields of its def, then the intro text.
TtlTrials.ORDER.forEach(wish => {
  var def = TtlTrials.DEFS[wish]
  var knobs = TtlData.trials[wish]
  Object.keys(knobs).forEach(k => { def[k] = knobs[k] })
  def.intro = def.intro(def)
})
