// Karma and life roles on Discord. A linked player's member gets exactly one of Life 1 / Life 2 (the Spirit
// Corridor still counts as Life 1 until the rebirth) and, once Life 1 has been judged, the role of their tier
// (Wanderer / Survivor / Hero / Legend). The dark path adds Fallen next to the tier role, so "Fallen Hero"
// shows as Hero + Fallen. Only the roles in design/data/discord.toml [roles] are touched (never Linked:
// sdlink owns it). Synced on login, Life 1 death, rebirth (discord.js) and every few minutes for everyone online.
// Ops: /ttl discordroles <player> [dry | expect <keys…>]  — dry prints the computed roles without Discord.
const TtlDiscordRoles = {
  // Role keys (design/data/discord.toml [roles]) the player should have, in a stable order.
  desired(player) {
    var keys = []
    var phase = TtlLife.phase(player)
    if (phase === 'life1' || phase === 'corridor') keys.push('life1')
    else if (phase === 'life2') keys.push('life2')
    var rec = TtlKarma.record(player)
    if (rec && phase) {
      var i = TtlKarma.tierIndex(rec.tier)
      if (i >= 0) keys.push(String(TtlKarma.tiers()[i].title).toLowerCase())
      if (rec.dark) keys.push('fallen')
    }
    return keys
  },

  // Managed role keys: everything in [roles] except Linked.
  managed() {
    return Object.keys(TtlData.discord.roles).filter(k => k !== 'linked')
  },

  sync(server, player) {
    var name = String(player.username)
    if (TtlDiscord.isBot(name)) return
    TtlHall.noteSoul(server, player)
    var guild = TtlSdlink.guild()
    if (!guild) return
    var id = TtlSdlink.discordId(player.getStringUUID())
    if (!id) return
    var want = {}
    this.desired(player).forEach(k => { want[k] = true })
    var self = this
    var apply = member => {
      try {
        if (member) self.apply(guild, member, want, name)
      } catch (e) {
        TtlSdlink.warn('roles', e)
      }
    }
    var cached = guild.getMemberById(id)
    if (cached) apply(cached)
    else guild.retrieveMemberById(id).queue(apply, e => TtlSdlink.warn('roles member', e))
  },

  // Runs on the server thread or a JDA thread: touches only Discord objects.
  apply(guild, member, want, name) {
    var has = {}
    member.getRoles().forEach(r => { has[String(r.getId())] = true })
    var roles = TtlData.discord.roles
    this.managed().forEach(key => {
      var role = guild.getRoleById(String(roles[key]))
      if (!role) return
      var on = !!has[String(role.getId())]
      if (want[key] && !on) {
        guild.addRoleToMember(member, role).queue(null, e => TtlSdlink.warn(`roles add ${key}`, e))
        console.info(`[ttl] discord roles: ${name} +${key}`)
      } else if (!want[key] && on) {
        guild.removeRoleFromMember(member, role).queue(null, e => TtlSdlink.warn(`roles remove ${key}`, e))
        console.info(`[ttl] discord roles: ${name} -${key}`)
      }
    })
  },

  syncAll(server) {
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        this.sync(server, p)
      } catch (e) {
        TtlSdlink.warn('roles sync', e)
      }
    })
  }
}

PlayerEvents.loggedIn(event => {
  var { player, server } = event
  server.scheduleInTicks(60, () => {
    try {
      TtlDiscordRoles.sync(server, player)
    } catch (e) {
      console.warn(`[ttl] discord roles: login sync failed for ${player.username}: ${e}`)
    }
  })
})

ServerEvents.loaded(event => {
  var server = event.server
  var ticks = Math.max(1, TtlData.discord.timing.role_sync_minutes) * 1200
  var loop = () => server.scheduleInTicks(ticks, () => {
    try {
      TtlDiscordRoles.syncAll(server)
    } catch (e) {
      console.error(`[ttl] discord roles: periodic sync failed: ${e}`)
    }
    loop()
  })
  loop()
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var run = (ctx, mode) => {
    try {
      var server = ctx.source.getServer()
      var target = Arguments.PLAYER.getResult(ctx, 'target')
      var keys = TtlDiscordRoles.desired(target)
      var label = keys.join(' ') || 'none'
      if (mode === 'expect') {
        var expected = String(Arguments.GREEDY_STRING.getResult(ctx, 'keys')).trim().split(/\s+/).join(' ')
        if (expected === 'none' ? keys.length : expected !== label) {
          ctx.source.sendSystemMessage(Text.red(`ttl: discordroles ${target.username} expected ${expected}, got ${label}`))
          return 0
        }
        ctx.source.sendSystemMessage(Text.of(`discordroles ${target.username}: ${label} (ok)`))
        return 1
      }
      var id = TtlSdlink.discordId(target.getStringUUID())
      var link = id ? `discord ${id}` : (TtlSdlink.load() ? 'not linked' : 'sdlink missing')
      if (mode === 'sync') TtlDiscordRoles.sync(server, target)
      ctx.source.sendSystemMessage(Text.of(`discordroles ${target.username}: ${label} [${link}]${mode === 'sync' ? ' synced' : ' (dry run)'}`))
      return 1
    } catch (e) {
      console.error(`[ttl] discordroles failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  event.register(Commands.literal('ttl')
    .then(Commands.literal('discordroles')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .executes(ctx => run(ctx, 'sync'))
        .then(Commands.literal('dry').executes(ctx => run(ctx, 'dry')))
        .then(Commands.literal('expect')
          .then(Commands.argument('keys', Arguments.GREEDY_STRING.create(event)).executes(ctx => run(ctx, 'expect')))))))
})
