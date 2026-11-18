// One call after a successful game transition. The transition owns its idempotency: two distinct
// victories, or a Legendary passing back to its first holder, are both news.
const TtlDiscordStory = {
  botCounts: {},

  post(server, kind, actors, text, testNation) {
    var seen = {}
    var test = !!testNation
    actors.forEach(actor => {
      var name = String(actor)
      if (!TtlDiscord.isBot(name) || seen[name]) return
      seen[name] = true
      test = true
      // Only connected test players have counters; an offline transfer giver can still suppress a post.
      var counts = this.botCounts[name]
      if (counts) counts[kind] = (counts[kind] || 0) + 1
    })
    if (!actors.length || test) return false
    return TtlDiscord.post(server, text)
  }
}

PlayerEvents.loggedIn(event => {
  var name = String(event.player.username)
  if (TtlDiscord.isBot(name)) TtlDiscordStory.botCounts[name] = {}
})
PlayerEvents.loggedOut(event => {
  delete TtlDiscordStory.botCounts[String(event.player.username)]
})

// An operator can assert the number of would-be lines in a bot's current session without contacting Discord.
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var expect = ctx => {
    var name = String(Arguments.PLAYER.getResult(ctx, 'target').username)
    var moment = String(Arguments.STRING.getResult(ctx, 'moment'))
    var want = Number(Arguments.INTEGER.getResult(ctx, 'count'))
    var counts = TtlDiscordStory.botCounts[name]
    var actual = counts ? Number(counts[moment] || 0) : -1
    var ok = !!counts && actual === want
    ctx.source.sendSystemMessage(Text.of(ok ? 'ok' : `ttl: ${name} ${moment} lines: expected ${want}, got ${actual}`))
    return ok ? 1 : 0
  }
  var arg = (name, type) => Commands.argument(name, type.create(event))
  event.register(Commands.literal('ttl').then(Commands.literal('discord').requires(src => src.hasPermission(2))
    .then(Commands.literal('expect').then(arg('target', Arguments.PLAYER)
      .then(arg('moment', Arguments.STRING).then(arg('count', Arguments.INTEGER).executes(expect)))))))
})
