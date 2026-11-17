// Quest book commands (Brigadier merges these into the /ttl tree from commands.js). Ops only.
//   /ttl quests check                         every chapter and quest in generated/quests.js (tools/gen_quests.py)
//                                             is loaded by FTB Quests; "ttl: ..." when one is missing
//   /ttl quests tick <player>                 run the Life 1 milestone check now (whispers.js, primer.js)
//   /ttl quests expect <player> said <id>     test assertion: the milestone whisper <id> was said this life
//   /ttl quests expect <player> primer yes|no test assertion: this life got the primer book
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] quests command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))

  var check = ctx => {
    var file = null
    var QOB = null
    try {
      file = Java.loadClass('dev.ftb.mods.ftbquests.quest.ServerQuestFile').INSTANCE
      QOB = Java.loadClass('dev.ftb.mods.ftbquests.quest.QuestObjectBase')
    } catch (e) {
      console.warn(`[ttl] quests: FTB Quests classes not reachable from scripts: ${e}`)
    }
    if (!file || !QOB) throw 'FTB Quests is not loaded (no ServerQuestFile)'
    var loaded = {}
    file.getAllChapters().forEach(ch => {
      loaded[String(QOB.getCodeString(ch))] = true
      ch.getQuests().forEach(q => { loaded[String(QOB.getCodeString(q))] = true })
    })
    var missing = []
    var count = 0
    Object.keys(TtlQuestIds).forEach(key => {
      var chapter = TtlQuestIds[key]
      if (!loaded[chapter.id]) missing.push(`chapter ${key}`)
      Object.keys(chapter.quests).forEach(q => {
        count++
        if (!loaded[chapter.quests[q]]) missing.push(`${key}/${q}`)
      })
    })
    if (missing.length) throw `${missing.length} quest object(s) not loaded: ${missing.slice(0, 8).join(', ')}`
    say(ctx, `quests ok: ${Object.keys(TtlQuestIds).length} chapters, ${count} quests loaded`)
    return 1
  }

  var tick = ctx => {
    var server = ctx.source.getServer()
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var primer = TtlPrimer.ensure(server, target)
    var said = TtlWhispers.check(server, target)
    say(ctx, `quests ${target.username}: primer ${primer ? 'given' : 'unchanged'}, whisper ${said || 'none'}`)
    return 1
  }

  var expect = ctx => {
    var target = Arguments.PLAYER.getResult(ctx, 'target')
    var field = String(Arguments.STRING.getResult(ctx, 'field'))
    var value = String(Arguments.STRING.getResult(ctx, 'value'))
    var data = target.persistentData
    var life = String(data.getLong('ttl.l1.start'))
    var actual
    if (field === 'said') {
      var said = TtlWhispers.said(target) || []
      actual = said.indexOf(value) >= 0 ? value : `not said (said: ${said.join(',') || 'nothing'})`
    } else if (field === 'primer') {
      actual = String(data.getString(TtlPrimer.KEY)) === life ? 'yes' : 'no'
    } else {
      throw `unknown field ${field} (said, primer)`
    }
    if (actual !== value) throw `${target.username}: ${field} expected ${value}, got ${actual}`
    say(ctx, `quests ${target.username}: ${field} = ${value} ok`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('quests')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('check').executes(logged(check)))
      .then(Commands.literal('tick')
        .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(tick))))
      .then(Commands.literal('expect')
        .then(Commands.argument('target', Arguments.PLAYER.create(event))
          .then(Commands.argument('field', Arguments.STRING.create(event))
            .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expect))))))))
})
