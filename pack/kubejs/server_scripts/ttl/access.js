// Who may join: Discord account linking (Simple Discord Link access control: /verify <code> in our Discord,
// membership required) replaces the manual whitelist. Fail-closed: while the Discord bot is not connected,
// sdlink cannot check anyone, so only players on the old whitelist file and ops may stay; others are told why.
// Test bots (TtlBot*) and ops are never kicked.
const TtlAccess = {
  allowedWithoutDiscord(server, player) {
    var list = server.getPlayerList()
    var profile = player.getGameProfile()
    // The whitelist file itself: isWhiteListed() on the player list says yes to everyone once the whitelist is off.
    return list.isOp(profile) || list.getWhiteList().isWhiteListed(profile)
  },

  check(server, player) {
    var name = String(player.username)
    if (TtlDiscord.isBot(name)) return
    var api = TtlDiscord.load()
    var ready = false
    try {
      ready = !!api && !!api.Bot.INSTANCE && api.Bot.INSTANCE.isBotReady()
    } catch (e) {
      ready = false
    }
    if (ready || this.allowedWithoutDiscord(server, player)) return
    console.warn(`[ttl] access: ${name} kicked, the Discord link is down and they are not on the whitelist`)
    server.runCommandSilent(`kick ${name} The Discord link is down right now, so new accounts can't be checked. Try again in a few minutes.`)
  }
}

PlayerEvents.loggedIn(event => {
  var { player, server } = event
  // sdlink's own check runs at login; this backstop runs once the player is in.
  server.scheduleInTicks(20, () => {
    try {
      TtlAccess.check(server, player)
    } catch (e) {
      console.error(`[ttl] access check failed for ${player.username}: ${e}`)
    }
  })
})
