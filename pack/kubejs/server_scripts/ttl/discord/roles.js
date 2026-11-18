// Karma and life roles on Discord. A linked player's member gets exactly one of Life 1 / Life 2 (the Spirit
// Corridor still counts as Life 1 until the rebirth) and, once Life 1 has been judged, the role of their tier
// (Wanderer / Survivor / Hero / Legend). The dark path adds Fallen next to the tier role, so "Fallen Hero"
// shows as Hero + Fallen. Fixed roles come from design/data/discord.toml [roles] (never Linked:
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
    if (TtlNations.isMember(player.getServer(), player)) keys.push('nation')
    return keys
  },

  // Managed role keys: everything in [roles] except Linked.
  managed() {
    return Object.keys(TtlData.discord.roles).filter(k => k !== 'linked' && k !== 'nation_prefix')
  },

  sync(server, player) {
    var name = String(player.username)
    if (TtlDiscord.isBot(name)) return
    TtlHall.noteSoul(server, player)
    var guild = TtlSdlink.guild()
    if (!guild) return
    var id = TtlSdlink.discordId(TtlLife.uuid(player))
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

  // Snapshot all verified accounts once, including offline players. A failed database read aborts
  // the pass so a temporary outage cannot be mistaken for everybody unlinking their account.
  nationPlan(server) {
    var api = TtlSdlink.load()
    if (!api || !TtlNations.manager()) return null
    var colorProperty = Java.loadClass('dev.ftb.mods.ftbteams.api.property.TeamProperties').COLOR
    var accounts = api.Db.INSTANCE.findAll(api.Account)
    var links = {}
    for (var i = 0; i < accounts.size(); i++) {
      var acc = accounts.get(i)
      if (!TtlDiscord.isBot(acc.getInGameName()) && acc.getDiscordID()) links[String(acc.getUuid())] = String(acc.getDiscordID())
    }
    // Unlike the read-only nation displays, deletion needs a successful parse, even on a damaged save.
    var all = JSON.parse(String(server.persistentData.getString(TtlNations.KEY)) || '{}')
    if (!all || typeof all !== 'object' || Array.isArray(all)) throw new Error('invalid nation records')
    var keys = Object.keys(all).sort((a, b) => Number(all[a].founded) - Number(all[b].founded) || a.localeCompare(b))
    var wanted = {}
    var cap = Number(TtlData.discord.limits.nation_roles)
    if (!Number.isInteger(cap) || cap < 0 || !TtlData.discord.roles.nation_prefix) throw new Error('invalid nation role configuration')
    for (var k = 0; k < keys.length && Object.keys(wanted).length < cap; k++) {
      var key = keys[k], rec = all[key]
      var team = TtlNations.teamByKey(key)
      if (!team) return null  // Nation cleanup will remove disbanded charters; retry ambiguous team reads.
      if (TtlDiscord.isBot(TtlNations.nameOfId(server, team.getOwner()))) continue
      var ids = []
      TtlNations.memberIdsOf(team).forEach(uuid => {
        var discord = links[String(uuid)]
        if (discord && ids.indexOf(discord) < 0) ids.push(discord)
      })
      wanted[key] = {name: String(TtlData.discord.roles.nation_prefix) + rec.name, members: ids,
        color: Number(team.getProperty(colorProperty).rgb()) & 0xffffff}
    }
    return wanted
  },

  // All persistentData reads and writes are on the Minecraft thread. Hold a pass open until
  // Discord answers; the next pass retries failures from the persisted ownership/membership ledger.
  nationBusy: false,

  syncNations(server) {
    if (this.nationBusy || TtlDiscord.muted(server)) return
    var guild = TtlSdlink.guild()
    if (!guild) return
    var plan = this.nationPlan(server)
    if (!plan) return
    var storage = 'ttl.discord.nationroles.' + guild.getId()
    var state = JSON.parse(String(server.persistentData.getString(storage)) || '{}')
    var save = () => server.persistentData.putString(storage, JSON.stringify(state))
    var pending = 1
    var finish = () => { if (--pending === 0) this.nationBusy = false }
    var request = (action, success, failure) => {
      pending++
      var done = fn => value => server.execute(() => {
        try { fn(value) } catch (e) { TtlSdlink.warn('nation role result', e) } finally { finish() }
      })
      try {
        action.queue(done(success), done(failure || (e => TtlSdlink.warn('nation role request', e))))
      } catch (e) {
        finish()
        throw e
      }
    }
    this.nationBusy = true
    try {
      var cap = Number(TtlData.discord.limits.nation_roles)
      // Pending creations and deletions count towards the cap until their outcome is known.
      Object.keys(plan).forEach(key => {
        if (!state[key] && Object.keys(state).length < cap) {
          state[key] = {pending: 'ttl-pending-' + Java.loadClass('java.util.UUID').randomUUID(), members: []}
          save()
        }
      })
      Object.keys(state).forEach(key => {
        try {
          var entry = state[key], want = plan[key]
          var role = entry.id ? guild.getRoleById(String(entry.id)) : null
          if (!role && !entry.id) {
            // A crash after Discord creates the role but before its ID is saved can be recovered by
            // this unique pre-recorded temporary name. Human-readable nation names never imply ownership.
            var matches = guild.getRolesByName(entry.pending, false)
            if (matches.size() > 1) { TtlSdlink.warn('ambiguous pending nation role', entry.pending); return }
            if (matches.size()) role = matches.get(0)
            if (!role && want) {
              var action = guild.createRole().setName(entry.pending)['setPermissions(java.lang.Long)'](0)
                .setHoisted(false).setMentionable(false)['setColor(java.lang.Integer)'](want.color)
              request(action, created => {
                entry.id = String(created.getId())
                save()
                request(created.getManager().setName(want.name), () => {})
                this.nationMembers(guild, created, entry, want.members, save, request)
              })
              return
            }
          }
          if (!role) { delete state[key]; save(); return }
          if (role.isManaged() || String(role.getId()) === String(guild.getId()) || Number(role.getPermissionsRaw()) !== 0 ||
              Object.keys(TtlData.discord.roles).some(k => String(TtlData.discord.roles[k]) === String(role.getId()))) {
            TtlSdlink.warn('nation role ownership', 'refusing to change protected role ' + role.getId())
            return
          }
          if (!entry.id) { entry.id = String(role.getId()); save() }
          if (!want) {
            request(role.delete(), () => { delete state[key]; save() })
            return
          }
          if (String(role.getName()) !== want.name) request(role.getManager().setName(want.name), () => {})
          if (role.getColorRaw() !== want.color) request(role.getManager()['setColor(int)'](want.color), () => {})
          if (role.isMentionable()) request(role.getManager().setMentionable(false), () => {})
          this.nationMembers(guild, role, entry, want.members, save, request)
        } catch (e) { TtlSdlink.warn('nation role sync ' + key, e) }
      })
    } finally { finish() }
  },

  nationMembers(guild, role, entry, wanted, save, request) {
    var snowflake = Java.loadClass('com.hypherionmc.sdlink.shaded.dv8tion.jda.api.entities.UserSnowflake')
    var cached = {}
    guild.getMembersWithRoles(role).forEach(member => { cached[String(member.getId())] = true })
    // JDA may only cache online members. Journal a grant before sending it so an offline leaver,
    // an account relink, or a restart can always revoke the previous recipient by Discord ID.
    wanted.forEach(id => {
      if (entry.members.indexOf(id) < 0) { entry.members.push(id); save() }
      if (!cached[id]) request(guild.addRoleToMember(snowflake['fromId(java.lang.String)'](id), role), () => {})
    })
    Object.keys(cached).forEach(id => {
      if (entry.members.indexOf(id) < 0) { entry.members.push(id); save() }
    })
    entry.members.slice().forEach(id => {
      if (wanted.indexOf(id) >= 0) return
      var forget = () => { entry.members = entry.members.filter(stored => stored !== id); save() }
      request(guild.removeRoleFromMember(snowflake['fromId(java.lang.String)'](id), role), forget, e => {
        if (e.getErrorCode && Number(e.getErrorCode()) === 10007) forget()  // Already left the guild.
        else TtlSdlink.warn('nation role removal', e)
      })
    })
  },

  syncAll(server) {
    try { this.syncNations(server) } catch (e) { TtlSdlink.warn('nation role sync', e) }
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
  var token = String(Java.loadClass('java.util.UUID').randomUUID())
  server.persistentData.putString('ttl.discord.roles.loop', token)
  var ticks = Math.max(1, TtlData.discord.timing.role_sync_minutes) * 1200
  var loop = () => server.scheduleInTicks(ticks, () => {
    if (String(server.persistentData.getString('ttl.discord.roles.loop')) !== token) return
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
      if (mode === 'nation') {
        var member = keys.indexOf('nation') >= 0
        ctx.source.sendSystemMessage(Text.of(member ? 'discordroles: nation (ok)' : 'ttl: discordroles expected nation'))
        return member ? 1 : 0
      }
      if (mode === 'expect') {
        var expected = String(Arguments.GREEDY_STRING.getResult(ctx, 'keys')).trim().split(/\s+/).join(' ')
        if (expected === 'none' ? keys.length : expected !== label) {
          ctx.source.sendSystemMessage(Text.red(`ttl: discordroles ${target.username} expected ${expected}, got ${label}`))
          return 0
        }
        ctx.source.sendSystemMessage(Text.of(`discordroles ${target.username}: ${label} (ok)`))
        return 1
      }
      var id = TtlSdlink.discordId(TtlLife.uuid(target))
      var link = id ? `discord ${id}` : (TtlSdlink.load() ? 'not linked' : 'sdlink missing')
      if (mode === 'sync') {
        TtlDiscordRoles.sync(server, target)
        if (!TtlDiscord.isBot(target.username)) TtlDiscordRoles.syncNations(server)
      }
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
        .then(Commands.literal('dry').executes(ctx => run(ctx, 'dry'))
          .then(Commands.literal('expect').then(Commands.literal('nation').executes(ctx => run(ctx, 'nation')))))
        .then(Commands.literal('expect')
          .then(Commands.argument('keys', Arguments.GREEDY_STRING.create(event)).executes(ctx => run(ctx, 'expect')))))))
})
