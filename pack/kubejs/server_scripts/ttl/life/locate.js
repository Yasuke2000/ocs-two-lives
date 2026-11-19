// /locate place <id>: every canon place of the Tensura world, next to vanilla's structure/biome/poi (Brigadier merges
// this `locate` literal into the vanilla node; the vanilla root requirement, op level 2, stays, and `place` repeats it).
// /ttl where <id>: the same for players (permission 0), only a compass direction and a rounded distance, never
// coordinates or a teleport suggestion.
//
// Places = every anchor of design/data/anchors.toml (TtlAnchors, generated/anchors.js: the road stops and spots too) plus
// every build and landmark that has no anchor of its own (the Mortal Realm builds, the Spirit Domain, the Walpurgis
// Hall ...) once it has a recorded placement. Where the place really stands: the placement the placers recorded
// (builds `ttl.build.<name>.at`, landmarks `ttl.landmark.<name>.at`, Tempest `ttl.tempest.arrival`, Dwargon
// `ttl.dwargon.gate`: the same lookup as /ttl build where and /ttl landmark where); the anchor until then.
// The players' list leaves out what is internal (spots, map = false, the arrival).
const TtlLocate = {
  PLAYER_KINDS: ['settlement', 'build', 'landmark', 'pin'],
  COMPASS_EN: ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'],
  COMPASS_NL: ['noorden', 'noordoosten', 'oosten', 'zuidoosten', 'zuiden', 'zuidwesten', 'westen', 'noordwesten'],

  anchors() {
    return typeof TtlAnchors !== 'undefined' ? TtlAnchors : {}
  },

  // "x y z" (integers, or x.5 y z.5) -> {x, y, z}, null when it is empty or not three numbers.
  parse(text) {
    var parts = String(text || '').trim().split(/\s+/).map(Number)
    if (parts.length !== 3 || parts.some(n => !isFinite(n))) return null
    return { x: Math.floor(parts[0]), y: Math.floor(parts[1]), z: Math.floor(parts[2]) }
  },

  stored(server, key) {
    return this.parse(server.persistentData.getString(key))
  },

  buildAt(server, b) {
    return this.parse(TtlBuilds.str(server, b, 'at'))
  },

  landmarkAt(server, l) {
    return this.stored(server, TtlLandmarks.key(l, 'at'))
  },

  // The recorded placement of an anchored place, or null.
  placedAt(server, id, a) {
    if (id === 'tempest') return this.stored(server, 'ttl.tempest.arrival')
    if (id === 'dwargon') return this.stored(server, 'ttl.dwargon.gate')
    if (a.build && typeof TtlBuilds !== 'undefined') {
      var b = TtlBuilds.find(a.build)
      return b ? this.buildAt(server, b) : null
    }
    if (a.landmark && typeof TtlLandmarks !== 'undefined') {
      var l = TtlLandmarks.find(a.landmark)
      return l ? this.landmarkAt(server, l) : null
    }
    return null
  },

  // {id, title, dim, x, y (null: not known), z, placed, kind}, or null for an unknown id.
  resolve(server, id) {
    var a = this.anchors()[id]
    if (a) {
      var at = this.placedAt(server, id, a)
      return { id: id, title: a.title, kind: a.kind, dim: 'minecraft:overworld', placed: !!at,
        x: at ? at.x : a.x, y: at ? at.y : null, z: at ? at.z : a.z }
    }
    var b = typeof TtlBuilds !== 'undefined' ? TtlBuilds.find(id) : null
    var bp = b ? this.buildAt(server, b) : null
    if (bp) return { id: id, title: String(b.title), kind: 'build', dim: String(b.dimension), placed: true, x: bp.x, y: bp.y, z: bp.z }
    var l = typeof TtlLandmarks !== 'undefined' ? TtlLandmarks.find(id) : null
    var lp = l ? this.landmarkAt(server, l) : null
    if (lp) return { id: id, title: String(l.title || l.name), kind: 'landmark', dim: 'minecraft:overworld', placed: true, x: lp.x, y: lp.y, z: lp.z }
    return null
  },

  // Every id /locate place completes: all anchors, then placed builds and landmarks without an anchor.
  ids(server) {
    var out = Object.keys(this.anchors())
    var seen = {}
    out.forEach(id => { seen[id] = 1 })
    var more = []
    if (typeof TtlBuilds !== 'undefined') TtlBuilds.all().forEach(b => { if (!seen[b.name] && this.buildAt(server, b)) more.push(b.name) })
    if (typeof TtlLandmarks !== 'undefined') TtlLandmarks.all().forEach(l => { if (!seen[l.name] && !more.includes(l.name) && this.landmarkAt(server, l)) more.push(l.name) })
    return out.concat(more).sort()
  },

  // What a player may ask about: named places of the map, not internal spots or the arrival.
  playerIds() {
    var all = this.anchors()
    return Object.keys(all).filter(id => all[id].map !== false && this.PLAYER_KINDS.includes(all[id].kind)).sort()
  },

  // 0..7, clockwise from north. +X is east, +Z south.
  sector(dx, dz) {
    var deg = Math.atan2(dx, -dz) * 180 / Math.PI
    return ((Math.round(deg / 45) % 8) + 8) % 8
  },

  // Rounded for players: nearest 50 below 1,000, nearest 100 from there.
  roughly(d) {
    return d < 1000 ? Math.max(50, Math.round(d / 50) * 50) : Math.round(d / 100) * 100
  },

  grouped(n, sep) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, sep)
  },

  // [english, dutch] sentence for a player at (px, pz); `title` is the place's name.
  bearing(title, px, pz, p) {
    var dx = p.x - px
    var dz = p.z - pz
    var d = Math.sqrt(dx * dx + dz * dz)
    if (d < 100) return [`${title} is very close, less than 100 blocks away.`, `${title} is heel dichtbij, minder dan 100 blokken ver.`]
    var n = this.roughly(d)
    var s = this.sector(dx, dz)
    return [`${title} lies about ${this.grouped(n, ',')} blocks ${this.COMPASS_EN[s]} of you.`,
      `${title} ligt ongeveer ${this.grouped(n, '.')} blokken ten ${this.COMPASS_NL[s]} van je.`]
  }
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] locate command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }

  var suggest = source => (ctx, builder) => {
    var typed = String(builder.getRemainingLowerCase())
    var server = ctx.source.getServer()
    source(server).forEach(id => {
      if (id.indexOf(typed) !== 0) return
      var r = TtlLocate.resolve(server, id)
      if (r && r.title) builder.suggest(id, Text.of(String(r.title)))
      else builder.suggest(id)
    })
    return builder.buildFuture()
  }

  var idOf = ctx => String(Arguments.STRING.getResult(ctx, 'id')).toLowerCase()
  var here = ctx => {
    var pos = ctx.source.getPosition()
    return { x: Math.floor(pos.x()), z: Math.floor(pos.z()), dim: String(ctx.source.getLevel().dimension().location()) }
  }

  var locate = ctx => {
    var id = idOf(ctx)
    var r = TtlLocate.resolve(ctx.source.getServer(), id)
    if (!r) {
      ctx.source.sendFailure(Text.red(`Unknown place '${id}'. Tab-complete /locate place for the list; builds and landmarks without an anchor only count once placed.`))
      return 0
    }
    var me = here(ctx)
    var same = me.dim === r.dim
    var tp = same ? `/tp @s ${r.x} ~ ${r.z}` : `/execute in ${r.dim} run tp @s ${r.x} ~ ${r.z}`
    var line = Text.of(`The nearest ${r.title} is at `)
      .append(Text.green(`[${r.x}, ~, ${r.z}]`).clickSuggestCommand(tp).hover(Text.of('Click to suggest the teleport command')))
    if (same) {
      line = line.append(Text.of(` (${Math.floor(Math.sqrt(Math.pow(r.x - me.x, 2) + Math.pow(r.z - me.z, 2)))} blocks away)`))
    } else {
      line = line.append(Text.of(` in ${r.dim} (you are in ${me.dim}: no distance)`))
    }
    if (!r.placed) line = line.append(Text.gray(' - planned spot, not placed yet'))
    ctx.source.sendSystemMessage(line)
    return 1
  }

  var where = ctx => {
    var me = here(ctx)
    var id = idOf(ctx)
    var server = ctx.source.getServer()
    var r = TtlLocate.playerIds().includes(id) ? TtlLocate.resolve(server, id) : null
    if (!r) {
      ctx.source.sendSystemMessage(Text.red(`You know of no place called '${id}'. / Je kent geen plaats met de naam '${id}'.`))
      return 0
    }
    if (me.dim !== r.dim) {
      ctx.source.sendSystemMessage(Text.gold('From here you cannot tell where anything in the Tensura world lies.'))
      ctx.source.sendSystemMessage(Text.gray('Vanaf hier kun je niet bepalen waar iets in de Tensura-wereld ligt.'))
      return 0
    }
    var said = TtlLocate.bearing(r.title, me.x, me.z, r)
    ctx.source.sendSystemMessage(Text.gold(said[0]))
    ctx.source.sendSystemMessage(Text.gray(said[1]))
    return 1
  }

  var list = ctx => {
    var ids = TtlLocate.playerIds()
    ctx.source.sendSystemMessage(Text.gold('/ttl where <place>: which way a known place lies. Places: ' + ids.join(', ')))
    ctx.source.sendSystemMessage(Text.gray('/ttl where <plaats>: in welke richting een bekende plaats ligt.'))
    return 1
  }

  event.register(Commands.literal('locate')
    .then(Commands.literal('place')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('id', Arguments.STRING.create(event))
        .suggests(suggest(server => TtlLocate.ids(server)))
        .executes(logged(locate)))))

  event.register(Commands.literal('ttl')
    .then(Commands.literal('where')
      .requires(src => src.hasPermission(0))
      .executes(logged(list))
      .then(Commands.argument('id', Arguments.STRING.create(event))
        .suggests(suggest(() => TtlLocate.playerIds()))
        .executes(logged(where)))))
})
