// priority: 70
// The guide pop-up: design/data/guide.toml (TtlData.guide) → ttl-portals `/ttlguide` → a Great Sage–style
// screen with pages (mod: guide/GuideScreen.java). Shown on demand and once per player at three moments: the
// first join (join.js), the soul's first arrival in the Spirit Corridor and the start of Life 2 (corridor_flow.js).
// Players: /ttl guide [set]           the guide (main), or another page set (corridor, life2)
//          /ttl talk                  what the Voice of the World NPC runs on right-click (voice_npc.js)
// Ops:     /ttl guideforget <player>  show the once-only guides again
//          /ttl npc [respawn]         where the Voice of the World NPC is; "ttl: ..." when it is missing
const TtlGuide = {
  SEEN: 'ttl.guide.seen',

  sets() {
    return Object.keys(TtlData.guide || {})
  },

  // /ttlguide comes with the ttl-portals release after 0.8.0; with an older mod the callers fall back (the Life screen opens).
  available(server) {
    try {
      return server.getCommands().getDispatcher().getRoot().getChild('ttlguide') != null
    } catch (e) {
      return true
    }
  },

  // `then`: a command the client runs when the player closes the guide ('' for none). False when nothing was sent.
  show(server, player, set, then) {
    if (!this.available(server)) {
      console.warn('[ttl] guide: /ttlguide is missing (ttl-portals too old), guide not shown')
      return false
    }
    var pages = (TtlData.guide || {})[set]
    if (!pages || !pages.length) {
      console.warn(`[ttl] guide: no page set '${set}'`)
      return false
    }
    var spec = {
      set: set,
      then: then || '',
      pages: pages.map(p => ({ title: String(p.title), lines: String(p.body).replace(/\s+$/, '').split(/\r?\n/) }))
    }
    server.runCommandSilent(`ttlguide ${player.username} ${JSON.stringify(spec)}`)
    return true
  },

  seen(player, set) {
    return String(player.persistentData.getString(this.SEEN)).split(',').indexOf(set) >= 0
  },

  // Shows the set unless this player has seen it before; true when it was shown.
  once(server, player, set, then) {
    if (this.seen(player, set) || !this.available(server)) return false
    var data = player.persistentData
    var seen = String(data.getString(this.SEEN))
    data.putString(this.SEEN, seen ? `${seen},${set}` : set)
    return this.show(server, player, set, then)
  },

  // The Voice of the World NPC: the current Corridor step, or the guide outside the Corridor.
  talk(server, player) {
    if (TtlLife.phase(player) !== 'corridor') {
      this.show(server, player, 'main', '')
      return
    }
    var data = player.persistentData
    var step = String(data.getString('ttl.step'))
    if (!step) {
      this.show(server, player, 'corridor', '')
      return
    }
    if (step === 'trial' && String(data.getString('ttl.wish')) !== 'knowledge') {
      TtlCorridor.voice(server, player.username, 'Your Trial is under way. Face it.')
      return
    }
    TtlCorridor.showStep(server, player)
  }
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] guide command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }

  var show = set => ctx => {
    var player = ctx.source.getPlayerOrException()
    var name = set || String(Arguments.STRING.getResult(ctx, 'set')).toLowerCase()
    if (!TtlGuide.show(ctx.source.getServer(), player, name, '')) {
      player.tell(Text.red(`No such guide. Try: ${TtlGuide.sets().join(', ')}`))
      return 0
    }
    return 1
  }

  var npc = ctx => {
    var found = TtlVoiceNpc.find(ctx.source.getServer())
    if (found.length === 0) throw 'the Voice of the World NPC is missing from the Spirit Corridor'
    var e = found[0]
    ctx.source.sendSystemMessage(Text.of(`Voice of the World NPC: ${found.length} at ${e.getX().toFixed(1)} ${e.getY().toFixed(1)} ${e.getZ().toFixed(1)} (version ${ctx.source.getServer().persistentData.getInt('ttl.voice.version')})`))
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('guide')
      .executes(logged(show('main')))
      .then(Commands.argument('set', Arguments.STRING.create(event)).executes(logged(show(null)))))
    .then(Commands.literal('talk').executes(logged(ctx => {
      TtlGuide.talk(ctx.source.getServer(), ctx.source.getPlayerOrException())
      return 1
    })))
    .then(Commands.literal('guideforget')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event)).executes(logged(ctx => {
        var target = Arguments.PLAYER.getResult(ctx, 'target')
        target.persistentData.remove(TtlGuide.SEEN)
        ctx.source.sendSystemMessage(Text.of(`${target.username} will see the once-only guides again`))
        return 1
      }))))
    .then(Commands.literal('npc')
      .requires(src => src.hasPermission(2))
      .executes(logged(npc))
      .then(Commands.literal('respawn').executes(logged(ctx => {
        TtlVoiceNpc.replace(ctx.source.getServer())
        return npc(ctx)
      })))))
})
