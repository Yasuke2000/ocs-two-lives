// priority: 90
// The Discord side of Simple Discord Link (sdlink 3.4.5) for our scripts: its JDA bot, the guild, and the
// Minecraft UUID → Discord id link that `/verify` stores (sdlink's DatabaseManager, collection
// "verifiedaccounts", class SDLinkAccount: getUuid / getInGameName / getDiscordID).
// Every call returns null when sdlink, its bot or the link is missing: callers then do nothing.
// JDA REST calls go out with .queue(): never block the server thread on Discord.
const TtlSdlink = {
  api: undefined,
  warned: {},

  load() {
    if (this.api !== undefined) return this.api
    try {
      this.api = {
        Db: Java.loadClass('com.hypherionmc.sdlink.core.managers.DatabaseManager'),
        Account: Java.loadClass('com.hypherionmc.sdlink.core.database.SDLinkAccount')
      }
    } catch (e) {
      this.api = null
      console.info(`[ttl] discord: sdlink account API not available, roles and links are off (${e})`)
    }
    return this.api
  },

  // Logs a Discord-side problem once per kind, so a missing permission doesn't flood the log.
  warn(kind, e) {
    if (this.warned[kind]) return
    this.warned[kind] = true
    console.warn(`[ttl] discord ${kind}: ${e}`)
  },

  jda() {
    var base = TtlDiscord.load()
    if (!base) return null
    try {
      var bot = base.Bot.INSTANCE
      if (!bot || !bot.isBotReady()) return null
      return bot.getJDA()
    } catch (e) {
      this.warn('jda', e)
      return null
    }
  },

  guild() {
    var jda = this.jda()
    if (!jda) return null
    try {
      return jda.getGuildById(String(TtlData.discord.guild))
    } catch (e) {
      this.warn('guild', e)
      return null
    }
  },

  channel(key) {
    var jda = this.jda()
    var id = TtlData.discord.channels[key]
    if (!jda || !id) return null
    try {
      return jda.getTextChannelById(String(id))
    } catch (e) {
      this.warn(`channel ${key}`, e)
      return null
    }
  },

  // The Discord id linked to a Minecraft UUID, or null (not linked, or sdlink missing).
  discordId(uuid) {
    var api = this.load()
    if (!api) return null
    try {
      var acc = api.Db.INSTANCE.findById(String(uuid), api.Account)
      if (!acc) return null
      var id = acc.getDiscordID()
      return id ? String(id) : null
    } catch (e) {
      this.warn('account lookup', e)
      return null
    }
  },

  // The Discord id linked to an in-game name (sdlink's own way to resolve linked commands), or null.
  discordIdByName(name) {
    var api = this.load()
    if (!api) return null
    try {
      var all = api.Db.INSTANCE.findAll(api.Account)
      var want = String(name).toLowerCase()
      for (var i = 0; i < all.size(); i++) {
        var acc = all.get(i)
        if (String(acc.getInGameName()).toLowerCase() === want && acc.getDiscordID()) return String(acc.getDiscordID())
      }
    } catch (e) {
      this.warn('account list', e)
    }
    return null
  },

  // The Discord user name for an id from the bot's cache, or the id itself.
  userName(id) {
    var jda = this.jda()
    try {
      var user = jda ? jda.getUserById(String(id)) : null
      return user ? String(user.getName()) : String(id)
    } catch (e) {
      return String(id)
    }
  }
}
