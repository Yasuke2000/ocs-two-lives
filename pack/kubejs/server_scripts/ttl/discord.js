// priority: 95
// Discord: our story events in the server's Discord, through the bot of Simple Discord Link (sdlink, a
// server-only mod; config pack/config/simple-discord-link/, setup in docs/server.md "Discord bot").
// sdlink itself relays chat both ways plus joins, leaves, deaths, advancements and server start/stop.
// TtlDiscord.post(server, text) sends one line as an sdlink CUSTOM message (its events channel). Without
// sdlink, or while its bot is not logged in (no token), every post is dropped silently.
// Callers: life/death.js (Life 1 death), life/corridor_flow.js (rebirth), karma/view.js (Legend verdict);
// boss kills are polled below from the karma stat objectives (karma.toml stats with `major = true`).
// Each story event is also noted for the weekly Hall of Souls and the #leaderboard (discord/hall.js) and
// re-syncs the player's Discord roles (discord/roles.js). Ids and timings: design/data/discord.toml.
const TtlDiscord = {
  BOSS_TICKS: 200,
  api: undefined,

  // The sdlink classes, or null when the mod is absent (looked up once).
  load() {
    if (this.api !== undefined) return this.api
    try {
      this.api = {
        Builder: Java.loadClass('com.hypherionmc.sdlink.api.messaging.discord.DiscordMessageBuilder'),
        Type: Java.loadClass('com.hypherionmc.sdlink.api.messaging.MessageType'),
        Bot: Java.loadClass('com.hypherionmc.sdlink.core.discord.BotController')
      }
    } catch (e) {
      this.api = null
      console.info(`[ttl] discord: Simple Discord Link not available, Discord posts are off (${e})`)
    }
    return this.api
  },

  // Test bots (/ttlbot spawn TtlBot...) never reach Discord; sdlink's [filtering] drops its own events for them.
  isBot(name) {
    return /^TtlBot/.test(String(name))
  },

  // Player names go out bold; Discord markdown in a name (e.g. under_scores) is escaped.
  name(name) {
    var escaped = String(name).replace(/([\\*_~|>`])/g, '\\$1')
    return '**' + escaped + '**'
  },

  // Test runs never reach Discord: `tools/server.sh test|test-all` sets `ttl.discord.muted` (`/ttl discord mute on|off`)
  // around every run, and while a test bot is online every post is dropped as well (era changes, wild bosses, nation
  // wars and event lines have no player to check `isBot` on). Dropped lines stay in the log for the test to read.
  muted(server) {
    try {
      if (server.persistentData.getBoolean('ttl.discord.muted')) return 'muted'
      var bots = 0
      server.getPlayerList().getPlayers().forEach(p => { if (TtlDiscord.isBot(p.username)) bots++ })
      if (bots > 0) return `${bots} test bot(s) online`
    } catch (e) {
      console.warn(`[ttl] discord: mute check failed: ${e}`)
    }
    return null
  },

  post(server, text) {
    var api = this.load()
    if (!api) return false
    var why = this.muted(server)
    if (why) {
      console.info(`[ttl] discord: dropped (${why}): ${String(text)}`)
      return false
    }
    try {
      var bot = api.Bot.INSTANCE
      if (!bot || !bot.isBotReady()) return false
      new api.Builder(api.Type.CUSTOM).message(String(text)).build().sendMessage()
      return true
    } catch (e) {
      console.warn(`[ttl] discord: post failed: ${e}`)
      return false
    }
  },

  // The online player with this name, or null.
  player(server, name) {
    try {
      return server.getPlayerList().getPlayerByName(String(name))
    } catch (e) {
      return null
    }
  },

  // Hall of Souls / leaderboard notes and role syncs never break the story line itself.
  also(what, fn) {
    try {
      fn()
    } catch (e) {
      console.warn(`[ttl] discord: ${what} failed: ${e}`)
    }
  },

  life1Death(server, name) {
    if (this.isBot(name)) return
    this.post(server, `${this.name(name)} died in their first life. Their soul drifts into the Spirit Corridor.`)
    var p = this.player(server, name)
    if (!p) return
    this.also('hall death', () => TtlHall.noteDeath(server, p))
    server.scheduleInTicks(40, () => this.also('role sync', () => TtlDiscordRoles.sync(server, p)))
  },

  reborn(server, name, race) {
    if (this.isBot(name)) return
    var article = /^[aeiou]/i.test(String(race)) ? 'an' : 'a'
    this.post(server, `${this.name(name)} was reborn as ${article} **${race}**.`)
    var p = this.player(server, name)
    if (!p) return
    this.also('hall rebirth', () => TtlHall.noteRebirth(server, p, String(race)))
    server.scheduleInTicks(40, () => this.also('role sync', () => TtlDiscordRoles.sync(server, p)))
  },

  legend(server, name, title) {
    if (this.isBot(name)) return
    this.post(server, `The Voice of the World: the soul of ${this.name(name)} enters the Spirit Corridor, judged **${title}**.`)
    this.also('hall legend', () => TtlHall.noteLegend(server, String(name), String(title)))
  },

  // Boss kills: compares each online player's `major` kill stats with the last sample. A player's first sample
  // after a server start only records, so old kills are never announced again.
  checkBosses(server, seen) {
    var majors = TtlKarma.stats().filter(s => s.major && s.criterion)
    var self = this
    server.getPlayerList().getPlayers().forEach(p => {
      var name = p.username
      if (self.isBot(name)) return
      var id = TtlLife.uuid(p)
      var before = seen[id]
      var now = {}
      majors.forEach(s => {
        now[s.key] = TtlKarma.value(server, p, s)
        if (before && now[s.key] > (before[s.key] || 0)) {
          self.post(server, `${self.name(name)} slew the ${s.label}!`)
          self.also('hall boss', () => TtlHall.noteBoss(server, String(name), String(s.label)))
        }
      })
      seen[id] = now
    })
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  if (!TtlDiscord.load()) return
  var seen = {}
  var loop = () => server.scheduleInTicks(TtlDiscord.BOSS_TICKS, () => {
    try {
      TtlDiscord.checkBosses(server, seen)
    } catch (e) {
      console.error(`[ttl] discord: boss check failed: ${e}`)
    }
    loop()
  })
  loop()
})

// /ttl discord mute on|off|status (ops): the test mute, set by tools/server.sh around every test run.
ServerEvents.commandRegistry(event => {
  var { commands: Commands } = event
  var op = src => src.hasPermission(2)
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] discord command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var setMute = on => ctx => {
    var server = ctx.source.getServer()
    server.persistentData.putBoolean('ttl.discord.muted', on)
    console.info(`[ttl] discord: posts ${on ? 'muted' : 'unmuted'} (test mute)`)
    ctx.source.sendSystemMessage(Text.of(`Discord posts ${on ? 'muted' : 'unmuted'}`))
    return 1
  }
  var status = ctx => {
    var why = TtlDiscord.muted(ctx.source.getServer())
    ctx.source.sendSystemMessage(Text.of(why ? `Discord posts are dropped: ${why}` : 'Discord posts go out'))
    return 1
  }
  event.register(Commands.literal('ttl')
    .then(Commands.literal('discord').requires(op)
      .then(Commands.literal('mute')
        .executes(logged(status))
        .then(Commands.literal('on').executes(logged(setMute(true))))
        .then(Commands.literal('off').executes(logged(setMute(false))))
        .then(Commands.literal('status').executes(logged(status))))))
})
