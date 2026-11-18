// priority: 60
// Party commands (Brigadier merges these into the /ttl tree; party.js has the logic). Creating, inviting, joining, leaving and
// kicking are FTB Teams' own (`/ftbteams party ...`, or the team button next to the quest book).
// Players: /ttl party                          your party: leader, members, the party's Oath, boss credit
// Ops:     /ttl party status <player>          the same lines for someone else
//          /ttl party poll                     run one join-lock pass now (the poll runs one every 3 seconds anyway)
//          /ttl party expect <player> <field> <a> [<b>]   test assertion: prints "ttl: ..." when it does not hold
//            in <yes|no> (in an FTB party team) · members <n> (online, the player included) · total <n> (every member, offline too)
//            owner <yes|no> · path <light|dark|none> (the party's Oath path) · cap <n> (FTB's max_party_size, 0 = none)
//            same <player> <yes|no> (both stand in the same party) · boss <n> (the roster size boss.js snapshots for the player)
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] party command failed: ${e}`)
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

  var status = target => ctx => {
    var p = target ? who(ctx) : ctx.source.getPlayerOrException()
    say(ctx, target ? `Party of ${p.username}:` : 'Your party:')
    TtlParty.lines(server(ctx), p).forEach(l => say(ctx, `  ${l}`))
    return 1
  }

  var poll = ctx => {
    var r = TtlParty.enforce(server(ctx))
    say(ctx, `party: checked ${r.checked}, turned away ${r.kicked}, took the party's Oath ${r.inherited}, set the party's Oath ${r.recorded}`)
    return 1
  }

  var yesno = v => (v ? 'yes' : 'no')

  var expect = ctx => {
    var s = server(ctx)
    var p = who(ctx)
    var field = word(ctx, 'field')
    var a = arg(ctx, 'a')
    var b = ''
    try {
      b = arg(ctx, 'b')
    } catch (e) {
      b = ''
    }
    var got
    var want = a
    var info = TtlParty.info(s, p)
    if (field === 'in') {
      got = yesno(!!info)
    } else if (field === 'members') {
      got = String(TtlParty.membersOf(s, p).length)
    } else if (field === 'total') {
      got = String(info ? info.members.length : 1)
    } else if (field === 'owner') {
      got = yesno(TtlParty.isOwner(s, p))
    } else if (field === 'path') {
      var party = info ? TtlParty.partyPath(s, info, null) : null
      got = party ? party.path : 'none'
    } else if (field === 'cap') {
      got = String(TtlParty.cap())
    } else if (field === 'same') {
      var other = s.getPlayerList().getPlayerByName(a)
      if (!other) throw `${a} is not online`
      var otherId = TtlParty.teamId(s, other)
      got = yesno(!!info && otherId !== '' && otherId === info.id)
      want = b
    } else if (field === 'boss') {
      if (typeof TtlBoss === 'undefined') throw 'the boss framework is not loaded'
      var seen = TtlBoss.partyOf(s, p)
      got = String(seen ? seen.members.length : 0)
    } else {
      throw `unknown field ${field} (in, members, total, owner, path, cap, same or boss)`
    }
    if (got !== want) throw `${p.username}: expected party ${field}${field === 'same' ? ' ' + a : ''} = ${want}, got ${got}`
    say(ctx, `party ${p.username}: ${field} ${a}${b ? ' ' + b : ''} as expected`)
    return 1
  }

  var playerArg = () => Commands.argument('target', Arguments.PLAYER.create(event))
  var strArg = name => Commands.argument(name, Arguments.STRING.create(event))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('party')
      .executes(logged(status(false)))
      .then(Commands.literal('status').requires(ops)
        .then(playerArg().executes(logged(status(true)))))
      .then(Commands.literal('poll').requires(ops).executes(logged(poll)))
      .then(Commands.literal('expect').requires(ops)
        .then(playerArg().then(strArg('field').then(strArg('a').executes(logged(expect))
          .then(strArg('b').executes(logged(expect)))))))))
})
