// priority: 60
// Story commands (Brigadier merges these into the /ttl tree; story.js has the logic, design/data/story.toml the words).
// Players: /ttl story                              your path, acts and marks
//          /ttl story oath                         open the Oath choice (chat buttons as a fallback)
//          /ttl story oath <light|dark|unaligned>  swear it (what the menu items run); a party leader's Oath binds the party
//          /ttl story talk <npc>                   what that NPC says to you now (what NPC dialog buttons run)
//          /ttl story fight <boss>                 start a boss fight from the story when you stand near its arena
//          /ttl story flip                         Atonement or Corruption, once per soul, when a quest has opened it
//          /ttl story capstone                     retry your personal Act VII after your team finishes the book
// Ops:     /ttl story status <player>              the same lines for someone else
//          /ttl story oath <path> <player>         swear for someone (skips the party leader and Legend checks)
//          /ttl story fight <boss> <player>        start the fight for that player from anywhere
//          /ttl story act <player> <n>             complete act n (quest command reward: `ttl story act @p 2`)
//          /ttl story flag <player> <flag>         set a story flag; unflag removes it
//          /ttl story set <player> <light|dark|none>   exact path without any deltas (fixing / test hook)
//          /ttl story reset <player>               forget all story state
//          /ttl story killrep <player> <boss>      apply that boss's kill cost (kill_rep in bosses.toml) as boss.js finish will (test hook)
//          /ttl story expect <player> <field> <a> [<b>]   test assertion: prints "ttl: ..." when it does not hold
//            path <light|dark|none> · score <0|1|2> (scoreboard ttl.path) · stage <name> <yes|no> · act <n> <yes|no>
//            acts <highest done> · flag <id> <yes|no> · flips <n> · unlocked <boss> <yes|no> · title <name> <yes|no>
//            talk <npc> <n> (1-based index of the [[npc.talk]] entry that would answer, 0 = none)
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] story command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var arg = (ctx, name) => String(Arguments.STRING.getResult(ctx, name))
  var word = (ctx, name) => arg(ctx, name).toLowerCase()
  var who = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var server = ctx => ctx.source.getServer()
  var ops = src => src.hasPermission(2)
  // A player-facing refusal: the soul reads it in red; the command fails.
  var refuse = (ctx, text) => {
    var player = ctx.source.getPlayer()
    if (player) player.tell(Text.red(text))
    else ctx.source.sendSystemMessage(Text.red(`ttl: ${text}`))
    return 0
  }

  var status = target => ctx => {
    var p = target ? who(ctx) : ctx.source.getPlayerOrException()
    say(ctx, target ? `Story of ${p.username}:` : 'Your story:')
    TtlStory.lines(p).forEach(l => say(ctx, `  ${l}`))
    return 1
  }

  var oathMenu = ctx => {
    var p = ctx.source.getPlayerOrException()
    var err = TtlStory.oathMenu(server(ctx), p)
    return err ? refuse(ctx, err) : 1
  }

  var oath = target => ctx => {
    var p = target ? who(ctx) : ctx.source.getPlayerOrException()
    var err = TtlStory.oath(server(ctx), p, word(ctx, 'path'), { force: target })
    if (err) return refuse(ctx, err)
    if (target) say(ctx, `story ${p.username}: swore the ${word(ctx, 'path')} Oath`)
    return 1
  }

  var talk = ctx => {
    var err = TtlStory.talk(server(ctx), ctx.source.getPlayerOrException(), word(ctx, 'npc'))
    return err ? refuse(ctx, err) : 1
  }

  var fight = target => ctx => {
    var p = target ? who(ctx) : ctx.source.getPlayerOrException()
    var err = TtlStory.fight(server(ctx), p, word(ctx, 'boss'), { force: target })
    if (err) {
      // Put in the arena queue (bosses/boss.js, WP-W2) is an answer, not a failure: no "ttl:" line for test-all.
      var queued = false
      try {
        queued = typeof TtlBoss !== 'undefined' && !!TtlBoss.queueEntry(server(ctx), word(ctx, 'boss'), TtlBoss.partyKey(server(ctx), p).id)
      } catch (e) {
        queued = false
      }
      if (!queued) return refuse(ctx, err)
      var asker = ctx.source.getPlayer()
      if (asker) asker.tell(Text.yellow(err))
      else say(ctx, `story ${p.username}: in line for ${word(ctx, 'boss')}: ${err}`)
      return 1
    }
    say(ctx, `story ${p.username}: ${word(ctx, 'boss')} is being summoned`)
    return 1
  }

  var flip = ctx => {
    var err = TtlStory.flip(server(ctx), ctx.source.getPlayerOrException())
    return err ? refuse(ctx, err) : 1
  }

  var capstone = ctx => {
    var p = ctx.source.getPlayerOrException()
    if (TtlStory.hasAct(p, 7)) {
      say(ctx, 'Your Act VII is already recorded.')
      return 1
    }
    if (!p.persistentData.getBoolean(TtlStory.K_CAPSTONE)) return refuse(ctx, 'Close The Seventh Entry in your quest book first.')
    var err = TtlStory.act(server(ctx), p, 7)
    return err ? refuse(ctx, err) : 1
  }

  var act = ctx => {
    var p = who(ctx)
    var n = Number(Arguments.INTEGER.getResult(ctx, 'n'))
    var err = TtlStory.act(server(ctx), p, n, {})
    if (err && n === 7) {
      p.tell(Text.red(err))
      return 0
    }
    if (err) throw err
    say(ctx, `story ${p.username}: act ${n} done`)
    return 1
  }

  var flag = on => ctx => {
    var p = who(ctx)
    var id = word(ctx, 'flag')
    var err = on ? TtlStory.flag(server(ctx), p, id, {}) : TtlStory.unflag(server(ctx), p, id)
    if (err) throw err
    say(ctx, `story ${p.username}: flag ${id} ${on ? 'set' : 'removed'}`)
    return 1
  }

  var set = ctx => {
    var p = who(ctx)
    var path = word(ctx, 'path')
    if (path !== 'light' && path !== 'dark' && path !== 'none') throw `path must be light, dark or none, got ${path}`
    if (path === 'none') p.persistentData.remove(TtlStory.K_PATH)
    else p.persistentData.putString(TtlStory.K_PATH, path)
    TtlStory.syncScoreboard(server(ctx), p)
    TtlStory.note(server(ctx), p, `path set to ${path} by ${ctx.source.getTextName()}`)
    say(ctx, `story ${p.username}: path ${path}`)
    return 1
  }

  var reset = ctx => {
    var p = who(ctx)
    TtlStory.clear(server(ctx), p)
    say(ctx, `story ${p.username}: story state forgotten`)
    return 1
  }

  var killrep = ctx => {
    var p = who(ctx)
    var boss = word(ctx, 'boss')
    var bossDef = TtlBoss.def(boss)
    if (!bossDef) throw `unknown boss ${boss}`
    if (!bossDef.kill_rep) throw `${boss} has no kill_rep in bosses.toml`
    say(ctx, `story ${p.username}: killing ${boss} costs ${TtlStory.onBossKill(server(ctx), p, boss) || 'nothing'}`)
    return 1
  }

  var yesno = v => (v ? 'yes' : 'no')

  var expect = ctx => {
    var p = who(ctx)
    var field = word(ctx, 'field')
    var a = arg(ctx, 'a')
    var b = ''
    try {
      b = arg(ctx, 'b')
    } catch (e) {
      b = ''
    }
    if (b === 'null') b = ''
    var got
    var want = a
    if (field === 'path') {
      got = TtlStory.path(p) || 'none'
    } else if (field === 'score') {
      var board = server(ctx).getScoreboard()
      var obj = board.getObjective(TtlStory.BOARD)
      var info = obj ? board.getPlayerScoreInfo(p, obj) : null
      got = String(info ? info.value() : 'missing')
    } else if (field === 'stage') {
      got = yesno(p.stages.has(a))
      want = b
    } else if (field === 'act') {
      got = yesno(TtlStory.hasAct(p, Number(a)))
      want = b
    } else if (field === 'acts') {
      got = String(TtlStory.actsDone(p))
    } else if (field === 'flag') {
      got = yesno(TtlStory.hasFlag(p, a))
      want = b
    } else if (field === 'flips') {
      got = String(TtlStory.flips(p))
    } else if (field === 'unlocked') {
      got = yesno(TtlStory.unlocked(server(ctx)).indexOf(a) >= 0)
      want = b
    } else if (field === 'talk') {
      var npc = TtlStory.npcDef(a)
      if (!npc) throw `unknown npc ${a}`
      var entry = TtlStory.pick(p, npc)
      got = String(entry ? npc.talk.indexOf(entry) + 1 : 0)
      want = b
    } else if (field === 'title') {
      got = yesno(String(p.persistentData.getString('ttl.titles') || '').split(',').indexOf(a) >= 0)
      want = b
    } else {
      throw `unknown field ${field} (path, score, stage, act, acts, flag, flips, unlocked, talk or title)`
    }
    if (got !== want) throw `${p.username}: expected ${field}${field === 'stage' || field === 'act' || field === 'flag' || field === 'unlocked' || field === 'title' || field === 'talk' ? ' ' + a : ''} = ${want}, got ${got}`
    say(ctx, `story ${p.username}: ${field} ${a}${b ? ' ' + b : ''} as expected`)
    return 1
  }

  var playerArg = () => Commands.argument('target', Arguments.PLAYER.create(event))
  var strArg = name => Commands.argument(name, Arguments.STRING.create(event))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('story')
      .executes(logged(status(false)))
      .then(Commands.literal('status').requires(ops)
        .then(playerArg().executes(logged(status(true)))))
      .then(Commands.literal('oath')
        .executes(logged(oathMenu))
        .then(strArg('path').executes(logged(oath(false)))
          .then(playerArg().requires(ops).executes(logged(oath(true))))))
      .then(Commands.literal('talk')
        .then(strArg('npc').executes(logged(talk))))
      .then(Commands.literal('fight')
        .then(strArg('boss').executes(logged(fight(false)))
          .then(playerArg().requires(ops).executes(logged(fight(true))))))
      .then(Commands.literal('flip').executes(logged(flip)))
      .then(Commands.literal('capstone').executes(logged(capstone)))
      // Test hooks: keep the server-wide unlocked-boss list as it was around a test that completes acts (an Act VII by a
      // test bot would otherwise unlock Veldora for everyone on staging). mark keeps the first snapshot until restore.
      .then(Commands.literal('testunlock').requires(ops)
        .then(Commands.literal('mark').executes(logged(ctx => {
          var d = server(ctx).persistentData
          if (!d.contains(`${TtlStory.UNLOCKED}.testmark`)) d.putString(`${TtlStory.UNLOCKED}.testmark`, JSON.stringify(TtlStory.unlocked(server(ctx))))
          say(ctx, 'story: unlocked bosses marked')
          return 1
        })))
        .then(Commands.literal('restore').executes(logged(ctx => {
          var d = server(ctx).persistentData
          var key = `${TtlStory.UNLOCKED}.testmark`
          if (d.contains(key)) {
            d.putString(TtlStory.UNLOCKED, String(d.getString(key)))
            d.remove(key)
          }
          say(ctx, `story: unlocked bosses restored (${TtlStory.unlocked(server(ctx)).join(', ') || 'none'})`)
          return 1
        })))
        // Repair: drop one boss a test bot unlocked before the mark/restore hooks existed.
        .then(Commands.literal('drop').then(strArg('boss').executes(logged(ctx => {
          var id = word(ctx, 'boss')
          var list = TtlStory.unlocked(server(ctx)).filter(b => b !== id)
          server(ctx).persistentData.putString(TtlStory.UNLOCKED, JSON.stringify(list))
          console.info(`[ttl] story: ${id} dropped from the unlocked bosses by an op`)
          say(ctx, `story: unlocked bosses now ${list.join(', ') || 'none'}`)
          return 1
        })))))
      .then(Commands.literal('act').requires(ops)
        .then(playerArg().then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(act)))))
      .then(Commands.literal('flag').requires(ops)
        .then(playerArg().then(strArg('flag').executes(logged(flag(true))))))
      .then(Commands.literal('unflag').requires(ops)
        .then(playerArg().then(strArg('flag').executes(logged(flag(false))))))
      .then(Commands.literal('set').requires(ops)
        .then(playerArg().then(strArg('path').executes(logged(set)))))
      .then(Commands.literal('killrep').requires(ops)
        .then(playerArg().then(strArg('boss').executes(logged(killrep)))))
      .then(Commands.literal('reset').requires(ops)
        .then(playerArg().executes(logged(reset))))
      .then(Commands.literal('expect').requires(ops)
        .then(playerArg().then(strArg('field').then(strArg('a').executes(logged(expect))
          .then(strArg('b').executes(logged(expect)))))))))
})
