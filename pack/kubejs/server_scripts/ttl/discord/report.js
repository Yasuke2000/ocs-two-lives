// Discord ?commands (sdlink [minecraftCommands], prefix "?"; who may run what: the permissions in
// pack/config/simple-discord-link/simple-discord-link.toml). sdlink runs the command on the server as a fake
// source named after the sender's linked Minecraft name (chat.useLinkedNames = true) and replies with the
// FIRST message the command sends, so every command here answers in one message.
//
// ?bugreport <text>  (Linked members) — a bug report from Discord. The GitHub issue is made by the ttl-portals
//   /bug command, which only works for a player in game (it attaches position, life, inventory and log). So:
//   linked player online → `/bug [from Discord, @name] <text>` runs as them right away; offline → the report
//   waits in server persistentData `ttl.discord.bugs` and is filed the next time they join.
// ?ttl staff status | registry  (modder role) — read-only overviews for staff; also usable in game by ops.
const TtlDiscordBugs = {
  KEY: 'ttl.discord.bugs',

  queue(server) {
    try {
      var raw = String(server.persistentData.getString(this.KEY))
      return raw ? JSON.parse(raw) : []
    } catch (e) {
      return []
    }
  },

  clean(text) {
    return String(text).replace(/[\u0000-\u001f\u007f§]/g, ' ').replace(/\s+/g, ' ').trim().substring(0, 400)
  },

  file(server, name, discord, text) {
    server.runCommandSilent(`execute as ${name} at ${name} run bug [from Discord, @${discord}] ${text}`)
    console.info(`[ttl] discord bug report from ${name} (@${discord}) filed through /bug`)
  },

  // Returns the reply for Discord.
  report(server, source, raw) {
    var name = String(source.getTextName())
    var text = this.clean(raw)
    if (!text) return 'Write what went wrong after ?bugreport.'
    if (TtlDiscord.isBot(name)) return 'Test bots cannot send reports.'
    var id = TtlSdlink.discordIdByName(name)
    if (!id) return 'Link your Minecraft account first (/verify), then try again.'
    var discord = TtlSdlink.userName(id).replace(/[^A-Za-z0-9_.]/g, '')
    var player = TtlDiscord.player(server, name)
    if (player) {
      this.file(server, name, discord, text)
      return `Thanks, ${name}! Filed as a GitHub issue through your character in game.`
    }
    var list = this.queue(server)
    list.push({ n: name, d: discord, t: text, at: Date.now() })
    while (list.length > 20) list.shift()
    server.persistentData.putString(this.KEY, JSON.stringify(list))
    console.info(`[ttl] discord bug report from ${name} (@${discord}) queued until they join`)
    return `Thanks, ${name}! Saved: it becomes a GitHub issue the next time you join the server.`
  },

  deliver(server, player) {
    var name = String(player.username)
    var list = this.queue(server)
    var mine = list.filter(r => r.n.toLowerCase() === name.toLowerCase())
    if (!mine.length) return
    server.persistentData.putString(this.KEY, JSON.stringify(list.filter(r => mine.indexOf(r) < 0)))
    // /bug allows one report a minute per player.
    mine.forEach((r, i) => server.scheduleInTicks(1 + i * 1300, () => this.file(server, name, r.d, r.t)))
  }
}

PlayerEvents.loggedIn(event => {
  var { player, server } = event
  server.scheduleInTicks(200, () => {
    try {
      TtlDiscordBugs.deliver(server, player)
    } catch (e) {
      console.error(`[ttl] discord bug delivery failed for ${player.username}: ${e}`)
    }
  })
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] discord command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }

  var staffStatus = ctx => {
    var server = ctx.source.getServer()
    var players = []
    server.getPlayerList().getPlayers().forEach(p => { if (!TtlDiscord.isBot(p.username)) players.push(p) })
    var lines = players.map(p => {
      var rec = TtlKarma.record(p)
      return `${p.username}: ${TtlLife.phase(p) || 'none'}${rec ? `, ${TtlKarmaView.title(rec)}` : ''}, ${TtlLife.dimensionOf(p)}`
    })
    ctx.source.sendSystemMessage(Text.of([`${players.length} online`].concat(lines).join('\n')))
    return 1
  }

  var staffRegistry = ctx => {
    var holders = TtlRegistry.holders(ctx.source.getServer())
    var lines = Object.keys(holders).sort().map(id => `${id} ${holders[id].length}/${TtlRegistry.capOf(id)}: ${holders[id].join(', ')}`)
    ctx.source.sendSystemMessage(Text.of(['Held uniques:'].concat(lines.length ? lines : ['none']).join('\n')))
    return 1
  }

  event.register(Commands.literal('bugreport')
    .requires(src => src.hasPermission(2))
    .then(Commands.argument('text', Arguments.GREEDY_STRING.create(event)).executes(logged(ctx => {
      var reply = TtlDiscordBugs.report(ctx.source.getServer(), ctx.source, Arguments.GREEDY_STRING.getResult(ctx, 'text'))
      ctx.source.sendSystemMessage(Text.of(reply))
      return 1
    }))))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('staff')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('status').executes(logged(staffStatus)))
      .then(Commands.literal('registry').executes(logged(staffRegistry)))))
})
