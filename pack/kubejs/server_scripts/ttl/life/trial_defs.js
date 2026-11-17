// priority: 86
// The ten Trials of the Soul, one per Last Wish. Each lives in its own arena in the Spirit Corridor,
// 100 blocks apart along x, so different trials can run at the same time.
// A trial: title + intro (shown at start), limit (seconds), passOnTimeout (survive-type trials),
// floorY, start (player spawn, relative to the arena origin), gear (item commands with {p}),
// build(b) (arena blocks), setup(ctx) (mobs/items at start), tick(ctx) → 'pass' | 'fail' | null (each second).
// ctx: { server, player, name, o: origin {x,y,z}, data: player.persistentData, seconds, run(cmd), at(x,y,z) }.
// Checks only use accessors verified in KubeJS 2101 (position, food level, inventory count, isShiftKeyDown,
// entity tags/isAlive); mob deaths are counted, never hooked (EntityEvents.death skips mobs here).
const TtlTrials = {
  ORDER: ['strength', 'vengeance', 'protection', 'knowledge', 'hunger', 'freedom', 'deceit', 'creation', 'dominion', 'survival'],
  ARENA_VERSION: 1,

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
      title: 'Trial of Strength', intro: 'Four waves. Stand your ground.', limit: 180,
      floor: 'minecraft:polished_andesite', start: [0, 1, -12],
      gear: ['iron_sword', 'shield', 'iron_helmet', 'iron_chestplate', 'iron_leggings', 'iron_boots', 'cooked_beef 8'],
      WAVES: [
        [['minecraft:zombie', 4]],
        [['minecraft:skeleton', 3], ['minecraft:spider', 2]],
        [['minecraft:husk', 3], ['minecraft:vindicator', 1]],
        [['minecraft:vindicator', 2, 'Echo of Your Last Breath'], ['minecraft:skeleton', 2]]
      ],
      setup(ctx) {
        ctx.data.putInt('ttl.trial.wave', -1)
      },
      tick(ctx) {
        var wave = ctx.data.getInt('ttl.trial.wave')
        if (wave >= 0 && TtlTrials.count(ctx, 'ttl_trial') > 0) return null
        if (wave + 1 >= this.WAVES.length) return 'pass'
        var spots = [[10, 10], [-10, 10], [10, -2], [-10, -2], [0, 12]]
        var i = 0
        this.WAVES[wave + 1].forEach(group => {
          for (var k = 0; k < group[1]; k++) {
            var s = spots[i++ % spots.length]
            TtlTrials.mob(ctx, group[0], s[0], s[1], group[2] ? { CustomName: TtlTrials.named(group[2]) } : null)
          }
        })
        ctx.data.putInt('ttl.trial.wave', wave + 1)
        ctx.server.runCommandSilent(`title ${ctx.name} actionbar {"text":"Wave ${wave + 2} of ${this.WAVES.length}","color":"red"}`)
        console.info(`[ttl] trial ${ctx.name}: strength wave ${wave + 2}`)
        return null
      }
    },

    vengeance: {
      title: 'Trial of Vengeance', intro: 'The one who killed you is here. Make it pay.', limit: 120,
      floor: 'minecraft:polished_blackstone', start: [0, 1, -12],
      gear: ['iron_sword', 'shield', 'iron_chestplate', 'iron_leggings', 'cooked_beef 4'],
      // Mobs that make a fair duel; anything else (creepers, players, the void) sends a vindicator.
      DUELISTS: ['minecraft:zombie', 'minecraft:husk', 'minecraft:drowned', 'minecraft:skeleton', 'minecraft:stray',
        'minecraft:spider', 'minecraft:cave_spider', 'minecraft:vindicator', 'minecraft:pillager', 'minecraft:witch',
        'minecraft:enderman', 'minecraft:piglin_brute', 'minecraft:wither_skeleton', 'minecraft:blaze', 'minecraft:zombified_piglin'],
      build(b) {
        b.fill(-6, 0, -6, 6, 0, 6, 'minecraft:crying_obsidian', 'outline')
      },
      setup(ctx) {
        var killer = ctx.data.getString('ttl.killer')
        var type = this.DUELISTS.indexOf(killer) >= 0 ? killer : 'minecraft:vindicator'
        TtlTrials.mob(ctx, type, 0, 4, {
          CustomName: TtlTrials.named('The One Who Killed You'),
          attributes: [{ id: 'minecraft:generic.max_health', base: 60 }],
          Health: 60,
          Tags: ['ttl_trial', 'ttl_nemesis']
        })
        console.info(`[ttl] trial ${ctx.name}: vengeance against ${type}`)
      },
      tick(ctx) {
        return ctx.seconds >= 2 && TtlTrials.count(ctx, 'ttl_nemesis') === 0 ? 'pass' : null
      }
    },

    protection: {
      title: 'Trial of Protection', intro: 'Keep them alive for 90 seconds.', limit: 90, passOnTimeout: true,
      floor: 'minecraft:grass_block', start: [0, 1, -4],
      gear: ['iron_sword', 'iron_chestplate', 'iron_leggings', 'cooked_beef 4'],
      build(b) {
        b.fill(-1, 0, -1, 1, 0, 1, 'minecraft:hay_block')
      },
      setup(ctx) {
        TtlTrials.mob(ctx, 'minecraft:villager', 0, 0, {
          NoAI: true,
          CustomName: TtlTrials.named('The One You Left Behind', 'green'),
          Tags: ['ttl_trial', 'ttl_ward']
        })
      },
      tick(ctx) {
        if (TtlTrials.count(ctx, 'ttl_ward') === 0) return 'fail'
        if (ctx.seconds % 15 === 1) {
          var corners = [[12, 12], [-12, 12], [12, -12], [-12, -12]]
          var n = 2 + Math.floor(ctx.seconds / 30)
          for (var i = 0; i < n; i++) {
            var c = corners[(i + ctx.seconds) % 4]
            TtlTrials.mob(ctx, i % 3 === 2 ? 'minecraft:vindicator' : 'minecraft:zombie', c[0], c[1])
          }
        }
        return null
      }
    },

    knowledge: {
      title: 'Trial of Knowledge', intro: 'Answer the Voice. Four of five must be right.', limit: 180,
      floor: 'minecraft:dark_oak_planks', start: [0, 1, 0], gear: [],
      QUESTIONS: [
        { q: 'A man died saving a stranger and woke as the weakest of monsters. What was he reborn as?', a: 'slime', options: ['slime', 'goblin', 'dragon'] },
        { q: 'Which skill gave him a voice that answers every question?', a: 'great_sage', options: ['predator', 'great_sage', 'gluttony'] },
        { q: 'What do all magic and skills in this world feed on?', a: 'magicules', options: ['souls', 'mana', 'magicules'] },
        { q: 'Who sealed the Storm Dragon in the cave three hundred years ago?', a: 'hero', options: ['hero', 'demon_lord', 'church'] },
        { q: 'The more of me you take, the more you leave behind. What am I?', a: 'footsteps', options: ['memories', 'footsteps', 'coins'] }
      ],
      build(b) {
        b.fill(-15, 1, -15, 15, 3, -15, 'minecraft:bookshelf')
        b.fill(-15, 1, 15, 15, 3, 15, 'minecraft:bookshelf')
        b.fill(-15, 1, -15, -15, 3, 15, 'minecraft:bookshelf')
        b.fill(15, 1, -15, 15, 3, 15, 'minecraft:bookshelf')
        b.fill(0, 1, 0, 0, 1, 0, 'minecraft:lectern')
      },
      setup(ctx) {
        ctx.data.putInt('ttl.trial.q', 0)
        ctx.data.putInt('ttl.trial.correct', 0)
        this.ask(ctx.server, ctx.name, 0)
      },
      ask(server, name, i) {
        var question = this.QUESTIONS[i]
        TtlCorridor.voice(server, name, `Question ${i + 1} of ${this.QUESTIONS.length}: ${question.q}`)
        TtlCorridor.buttons(server, name, 'Your answer:', question.options.map(o => ({
          label: TtlCorridor.title(o), command: `/ttl answer ${o}`, hover: 'Answer'
        })))
      },
      // Called by /ttl answer. Returns an error message or null.
      answer(server, player, word) {
        var data = player.persistentData
        var i = data.getInt('ttl.trial.q')
        if (i >= this.QUESTIONS.length) return 'No question is waiting.'
        if (word === this.QUESTIONS[i].a) data.putInt('ttl.trial.correct', data.getInt('ttl.trial.correct') + 1)
        data.putInt('ttl.trial.q', i + 1)
        if (i + 1 < this.QUESTIONS.length) this.ask(server, player.username, i + 1)
        return null
      },
      tick(ctx) {
        if (ctx.data.getInt('ttl.trial.q') < this.QUESTIONS.length) return null
        return ctx.data.getInt('ttl.trial.correct') >= 4 ? 'pass' : 'fail'
      }
    },

    hunger: {
      title: 'Trial of Hunger', intro: 'You are starving. Eat until you are full before time runs out.', limit: 90,
      floor: 'minecraft:coarse_dirt', start: [0, 1, 0], gear: ['wooden_sword'],
      setup(ctx) {
        ctx.player.getFoodData().setFoodLevel(4)
        var food = [['minecraft:bread', 1, 10, 10], ['minecraft:bread', 1, -10, 10], ['minecraft:bread', 1, 0, -12],
          ['minecraft:apple', 1, 12, -6], ['minecraft:apple', 1, -12, -6], ['minecraft:cooked_porkchop', 1, 6, 13],
          ['minecraft:cooked_porkchop', 1, -6, -13], ['minecraft:carrot', 2, 13, 0], ['minecraft:carrot', 2, -13, 0]]
        food.forEach(f => TtlTrials.item(ctx, f[0], f[1], f[2], f[3]))
        TtlTrials.mob(ctx, 'minecraft:spider', 8, 8)
        TtlTrials.mob(ctx, 'minecraft:spider', -8, -8)
      },
      tick(ctx) {
        return ctx.player.getFoodData().getFoodLevel() >= 20 ? 'pass' : null
      }
    },

    freedom: {
      title: 'Trial of Freedom', intro: 'Reach the golden platform. Fall, and you start over.', limit: 150,
      floorY: -6, floor: 'minecraft:smooth_stone', start: [0, 1, -13], gear: [],
      // Jump course over a pit: [x, y, z] blocks relative to the origin, 1-2 block gaps, a few steps up.
      COURSE: [[0, 0, -9], [0, 0, -6], [1, 1, -4], [1, 1, -1], [0, 2, 1], [0, 2, 4], [-1, 1, 7], [0, 0, 10]],
      build(b) {
        b.fill(-1, 0, -15, 1, 0, -12, 'minecraft:quartz_block')
        this.COURSE.forEach(c => b.fill(c[0], c[1], c[2], c[0], c[1], c[2], 'minecraft:quartz_pillar'))
        b.fill(-1, 0, 12, 1, 0, 14, 'minecraft:gold_block')
      },
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
      title: 'Trial of Deceit', intro: 'Reach the emerald exit unseen. Watchers see anyone who walks upright near them: sneak.', limit: 150,
      floor: 'minecraft:deepslate_tiles', start: [0, 1, -14], gear: [],
      RADIUS: 7.5,
      // Watcher rows (z): the start (z -14) is out of sight of the first row, the exit is checked first.
      ROWS: [-4, 3, 10],
      build(b) {
        b.fill(-1, 0, 13, 1, 0, 15, 'minecraft:emerald_block')
      },
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
        var r = this.RADIUS
        this.ROWS.forEach(wz => [-8, 0, 8].forEach(wx => {
          if (Math.sqrt((dx - wx) * (dx - wx) + (dz - wz) * (dz - wz)) <= r) seen = true
        }))
        if (!seen) return null
        var strikes = ctx.data.getInt('ttl.trial.strikes') + 1
        ctx.data.putInt('ttl.trial.strikes', strikes)
        if (strikes >= 3) return 'fail'
        ctx.server.runCommandSilent(`execute in ${TtlLife.CORRIDOR} run tp ${ctx.name} ${ctx.o.x + 0.5} ${ctx.o.y + 1} ${ctx.o.z - 13.5} 0 0`)
        ctx.server.runCommandSilent(`title ${ctx.name} actionbar {"text":"Seen! ${3 - strikes} chance(s) left. Sneak.","color":"red"}`)
        return null
      }
    },

    creation: {
      title: 'Trial of Creation', intro: 'Gather what lies around you and craft a Lantern.', limit: 150,
      floor: 'minecraft:oak_planks', start: [0, 1, -6], gear: [],
      build(b) {
        b.fill(0, 1, 0, 0, 1, 0, 'minecraft:crafting_table')
      },
      setup(ctx) {
        var parts = [['minecraft:iron_ingot', 1, 12, 12], ['minecraft:coal', 1, -12, 10], ['minecraft:stick', 1, 10, -12],
          ['minecraft:cobblestone', 4, -10, -12], ['minecraft:string', 2, 13, 0], ['minecraft:flint', 1, -13, 0]]
        parts.forEach(i => TtlTrials.item(ctx, i[0], i[1], i[2], i[3]))
      },
      tick(ctx) {
        return ctx.player.inventory.count('minecraft:lantern') > 0 ? 'pass' : null
      }
    },

    dominion: {
      title: 'Trial of Dominion', intro: 'Bring three of the herd into the pen.', limit: 180,
      floor: 'minecraft:grass_block', start: [0, 1, 0], gear: ['lead 4', 'wheat 16'],
      PEN: { x1: 9, z1: 9, x2: 13, z2: 13 },
      build(b) {
        b.fill(8, 1, 8, 14, 1, 8, 'minecraft:oak_fence')
        b.fill(8, 1, 14, 14, 1, 14, 'minecraft:oak_fence')
        b.fill(8, 1, 8, 8, 1, 14, 'minecraft:oak_fence')
        b.fill(14, 1, 8, 14, 1, 14, 'minecraft:oak_fence')
        b.fill(8, 1, 11, 8, 1, 11, 'minecraft:oak_fence_gate[facing=east]')
      },
      setup(ctx) {
        ;[[-10, -10], [-12, -6], [-6, -12], [-12, -12], [-8, -8]].forEach(c => TtlTrials.mob(ctx, 'minecraft:cow', c[0], c[1], { Tags: ['ttl_trial', 'ttl_herd'] }))
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
        return inside >= 3 ? 'pass' : null
      }
    },

    survival: {
      title: 'Trial of Survival', intro: 'No weapons. Live for two minutes.', limit: 120, passOnTimeout: true,
      floor: 'minecraft:cobblestone', start: [0, 1, 0], gear: [],
      setup(ctx) {
        TtlTrials.mob(ctx, 'minecraft:skeleton', 12, 12)
        TtlTrials.mob(ctx, 'minecraft:skeleton', -12, -12)
      },
      tick(ctx) {
        if (ctx.seconds % 8 !== 4) return null
        var n = ctx.name
        var hazard = Math.floor(ctx.seconds / 8) % 3
        if (hazard === 0) ctx.server.runCommandSilent(`effect give ${n} minecraft:poison 5 0`)
        if (hazard === 1) ctx.run(`execute at ${n} run summon minecraft:falling_block ~ ~9 ~ {BlockState:{Name:"minecraft:anvil"},Time:1,DropItem:0b,HurtEntities:1b,FallHurtMax:6,FallHurtAmount:1.0f}`)
        if (hazard === 2) ctx.run(`execute at ${n} run setblock ~ ~ ~ minecraft:fire`)
        return null
      }
    }
  }
}
