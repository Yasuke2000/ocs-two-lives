// priority: 72
// Side content, shared helpers (design/data/sidequests.toml -> TtlData.sidequests): where a [[place]] is in the world, the
// canon-continent test (rule R11) and spawning / finding / removing the Easy NPCs of the side content.
//
//   TtlSidePlaces.resolve(server, id|place, offset, flat)  {dim, x, y, z} or null while its anchor is not placed;
//                                     offset = [x, y, z] in the place's own anchor (an inn), flat = skip the surface lookup
//   TtlSidePlaces.onContinent(x, z)   TtlWorld.onContinent when the world package is loaded, else the canon grid's owner
//                                     cell (the same test, world-state.md §2.0); true when no grid can be read
//   TtlSidePlaces.near(player, pos, r)  same dimension and within r blocks (horizontal)
//   TtlSideNpc.spawn(server, pos, preset, tags)   imports an Easy NPC preset there and tags the new entity; entity or null
//   TtlSideNpc.byUuid(server, dim, id)            a loaded entity by UUID string, or null
//   TtlSideNpc.remove(server, e)                  `/easy_npc delete` (Easy NPC keeps its own record) and discard
//   TtlSideNpc.cmd(server, e, rest)               `/easy_npc <rest with {npc} = the entity's UUID>`
const TtlSidePlaces = {
  OVERWORLD: 'minecraft:overworld',
  warned: {},

  conf() {
    return TtlData.sidequests
  },

  all() {
    return this.conf().place || []
  },

  get(id) {
    var all = this.all()
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return null
  },

  title(id) {
    var p = this.get(id)
    return p ? String(p.title) : String(id)
  },

  // ---- continent (R11) ----

  onContinent(x, z) {
    try {
      if (typeof TtlWorld !== 'undefined' && typeof TtlWorld.onContinent === 'function') return !!TtlWorld.onContinent(x, z)
    } catch (e) {
      // fall through to the grid
    }
    try {
      var g = Java.loadClass('com.yasuke.ttl.world.CanonMap').grid()
      if (!g) return true
      var o = g.ownerCell(Math.floor(x), Math.floor(z))
      var c = typeof o === 'number' ? String.fromCharCode(o) : String(o)
      return c !== '\u0000' && c !== '0' && c !== ''
    } catch (e2) {
      if (!this.warned.grid) console.warn(`[ttl] side: the canon grid is not readable, every place counts as on the continent: ${e2}`)
      this.warned.grid = true
      return true
    }
  },

  // ---- positions ----

  xyz(text) {
    var p = String(text || '').trim().split(/\s+/).map(Number)
    return p.length === 3 && p.every(n => !isNaN(n)) ? p : null
  },

  buildCorner(server, name) {
    var pd = server.persistentData
    if (pd.getInt(`ttl.build.${name}.version`) < 1) return null
    return this.xyz(pd.getString(`ttl.build.${name}.corner`))
  },

  isLoaded(server, dim, x, z) {
    return TtlCmd.run(server, `execute in ${dim} if loaded ${Math.floor(x)} 64 ${Math.floor(z)}`) > 0
  },

  // The y of the highest solid block's top (trees skipped) at a LOADED column, or null.
  surfaceY(server, dim, x, z) {
    if (!this.isLoaded(server, dim, x, z)) return null
    try {
      var Types = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types')
      return Number(server.getLevel(dim).getHeight(Types.MOTION_BLOCKING_NO_LEAVES, Math.floor(x), Math.floor(z)))
    } catch (e) {
      console.error(`[ttl] side: reading the surface at ${x} ${z} failed: ${e}`)
      return null
    }
  },

  landmarkPlanned(name) {
    var all = (TtlData.landmarks && TtlData.landmarks.landmark) || []
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].name) === String(name) && all[i].x !== undefined) return [Number(all[i].x), 64, Number(all[i].z)]
    }
    return null
  },

  // {dim, x, y, z} (block centre) or null. `offset` replaces the place's own x/y/z (an inn of the same anchor). `flat`
  // skips the heightmap of surface places (distance tests need only x/z; y is then 64).
  resolve(server, ref, offset, flat) {
    var p = typeof ref === 'string' ? this.get(ref) : ref
    if (!p) return null
    var dim = this.OVERWORLD
    var o = offset || [Number(p.x || 0), Number(p.y || 0), Number(p.z || 0)]
    var pd = server.persistentData
    var a = String(p.anchor)
    var x
    var y
    var z
    var surface = false
    if (a === 'tempest') {
      var t = this.xyz(pd.getString('ttl.tempest.arrival'))
      if (!t) return null
      x = Math.floor(t[0]) + o[0] + 0.5
      y = Math.floor(t[1]) + o[1]
      z = Math.floor(t[2]) + o[2] + 0.5
    } else if (a === 'build') {
      var c = this.buildCorner(server, String(p.build))
      if (!c) return null
      x = c[0] + o[0] + 0.5
      y = c[1] + o[1]
      z = c[2] + o[2] + 0.5
    } else if (a === 'build_at') {
      if (pd.getInt(`ttl.build.${p.build}.version`) < 1) return null
      var at = this.xyz(pd.getString(`ttl.build.${p.build}.at`))
      if (!at) return null
      x = Math.floor(at[0]) + 0.5
      y = Math.floor(at[1])
      z = Math.floor(at[2]) + 0.5
    } else if (a === 'dwargon') {
      try {
        if (typeof TtlDwargon === 'undefined' || typeof TTL_DWARGON_VERSION === 'undefined') return null
        if (pd.getInt('ttl.dwargon.version') !== TTL_DWARGON_VERSION) return null
        var b = TtlDwargon.box()
        x = b.x0 + o[0] + 0.5
        y = pd.getInt('ttl.dwargon.base') + o[1]
        z = b.z0 + o[2] + 0.5
      } catch (e) {
        return null
      }
    } else if (a === 'landmark') {
      var lm = this.xyz(pd.getString(`ttl.landmark.${p.landmark}.at`)) || this.landmarkPlanned(p.landmark)
      if (!lm) return null
      x = Math.floor(lm[0]) + 0.5
      y = Math.floor(lm[1])
      z = Math.floor(lm[2]) + 0.5
      surface = true
    } else {
      x = Number(p.x) + 0.5
      y = 64
      z = Number(p.z) + 0.5
      surface = true
    }
    var pos = { dim: dim, x: x, y: y, z: z, surface: surface }
    if (surface && !flat) {
      var sy = this.surfaceY(server, dim, x, z)
      if (sy === null) return null
      pos.y = sy
    }
    return pos
  },

  near(player, pos, r) {
    if (!pos || TtlLife.dimensionOf(player) !== String(pos.dim)) return false
    var dx = player.getX() - pos.x
    var dz = player.getZ() - pos.z
    return dx * dx + dz * dz <= r * r
  },

  dist(ax, az, bx, bz) {
    var dx = ax - bx
    var dz = az - bz
    return Math.sqrt(dx * dx + dz * dz)
  },

  // The nearest discover place within r of the player, or null (for `/ttl sidequest offers`).
  placesNear(server, player, r) {
    var out = []
    var self = this
    this.all().forEach(p => {
      var pos = self.resolve(server, p, null, true)
      if (pos && self.near(player, pos, r)) out.push(p)
    })
    return out
  }
}

const TtlSideNpc = {
  uuidOf(e) {
    try {
      var id = String(e.uuid)
      if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id)) return id
    } catch (x) {
      // fall through
    }
    return ''
  },

  hasTag(e, tag) {
    try {
      return e.getTags().contains(tag)
    } catch (x) {
      return false
    }
  },

  byUuid(server, dim, id) {
    if (!id) return null
    try {
      var U = Java.loadClass('java.util.UUID')
      var level = server.getLevel(dim || TtlSidePlaces.OVERWORLD)
      var e = level['getEntity(java.util.UUID)'](U.fromString(String(id)))
      return e || null
    } catch (x) {
      return null
    }
  },

  cmd(server, e, rest) {
    var id = typeof e === 'string' ? e : this.uuidOf(e)
    if (!id) return 0
    return TtlCmd.run(server, `easy_npc ${String(rest).replace('{npc}', id)}`)
  },

  remove(server, e) {
    if (!e) return
    var id = this.uuidOf(e)
    if (id && String(e.type).startsWith('easy_npc:')) TtlCmd.run(server, `easy_npc delete ${id}`)
    try {
      if (e.isAlive()) e.discard()
    } catch (x) {
      // already gone
    }
  },

  // Imports `easy_npc:preset/<preset>.npc.snbt` at pos and tags the nearest untagged Easy NPC (the new one). Entity or null.
  spawn(server, pos, preset, tags) {
    var file = `easy_npc:preset/${preset}.npc.snbt`
    var r = TtlCmd.run(server, `execute in ${pos.dim} run easy_npc preset import_new custom ${file} ${pos.x} ${pos.y} ${pos.z}`)
    if (!(r > 0)) {
      console.error(`[ttl] side: importing ${file} at ${pos.dim} ${pos.x} ${pos.y} ${pos.z} failed (result ${r})`)
      return null
    }
    var best = null
    var bestD = 4
    server.getLevel(pos.dim).getEntities().forEach(e => {
      if (!String(e.type).startsWith('easy_npc:')) return
      var t = e.getTags().toArray()
      for (var i = 0; i < t.length; i++) {
        if (String(t[i]).startsWith('ttl.')) return
      }
      var dx = e.getX() - pos.x
      var dy = e.getY() - pos.y
      var dz = e.getZ() - pos.z
      var d = dx * dx + dy * dy + dz * dz
      if (d < bestD) {
        best = e
        bestD = d
      }
    })
    if (!best) {
      console.error(`[ttl] side: ${file} was imported but no untagged Easy NPC stands within 2 blocks of ${pos.x} ${pos.y} ${pos.z}`)
      return null
    }
    tags.forEach(t => best.addTag(String(t)))
    return best
  },

  // Max health and a full heal (vanilla attribute command; the preset keeps Easy NPC's defaults otherwise).
  health(server, e, hp) {
    var id = this.uuidOf(e)
    if (!id || !(hp > 0)) return
    TtlCmd.run(server, `attribute ${id} minecraft:generic.max_health base set ${hp}`)
    try {
      e.setHealth(Number(hp))
    } catch (x) {
      console.warn(`[ttl] side: healing ${id} failed: ${x}`)
    }
  }
}
