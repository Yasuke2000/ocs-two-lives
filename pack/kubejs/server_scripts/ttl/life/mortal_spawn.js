// Wayfarer's Rest in the Mortal Realm. The saved Y is the player's feet, one block above the plaza.
// Keep the template origin at (-14, Y-7, -14) on upgrades: (0,0) is underneath the bell roof.
const TTL_MORTAL_SPAWN_VERSION = 2

const TtlMortalSpawn = {
  margin: 4,
  footprintColumns: null,

  // Ordinary players can still use doors, beds and the bell, walk the roads, and build outside
  // this particular installation. Protect only its authored columns and vertical extent.
  protectedBlock(player, block) {
    if (!player || String(player.type) !== 'minecraft:player' || TtlLife.dimensionOf(player) !== TtlLife.MORTAL) return false
    var x = block.x + 14, z = block.z + 14
    if (x < 0 || z < 0 || x >= 39 || z >= 39 || player.hasPermissions(2)) return false
    var data = player.getServer().persistentData
    if (data.getInt('ttl.mortal.version') !== TTL_MORTAL_SPAWN_VERSION) return false
    var localY = block.y - (data.getInt('ttl.mortal.y') - 7)
    if (localY < 0 || localY >= 22) return false
    var f = TtlMortalSpawnFootprint
    if (!this.footprintColumns) this.footprintColumns = TtlBuilds.decode(f.fill, 39 * 39)
    return this.footprintColumns[z * 39 + x] !== f.none
  },

  // Load FULL chunks synchronously on the server thread. The normal short-lived load ticket covers this
  // placement within the same tick and leaves every administrator's persistent /forceload flag intact.
  chunks(level) {
    for (var cx = -2; cx <= 1; cx++) {
      for (var cz = -2; cz <= 1; cz++) level.getChunk(cx, cz)
    }
  },

  run(server, cmd) {
    // world_reset.js also calls place(), bracketed by the old rectangular preload commands.
    if (cmd === 'forceload add -16 -16 16 16') {
      this.chunks(server.getLevel(TtlLife.MORTAL))
      return 1
    }
    if (cmd === 'forceload remove -16 -16 16 16') return 1
    return TtlCmd.run(server, `execute in ${TtlLife.MORTAL} run ${cmd}`)
  },

  // Distances are measured from authored solid columns, including inside the template's empty corners.
  distances(low, f) {
    var m = this.margin
    var w = f.size[0] + 2 * m
    var distances = new Array(w * (f.size[2] + 2 * m))
    for (var i = 0; i < low.length; i++) {
      if (low[i] === f.none) continue
      var x = i % f.size[0] + m
      var z = Math.floor(i / f.size[0]) + m
      for (var dz = -m; dz <= m; dz++) {
        for (var dx = -m; dx <= m; dx++) {
          var d = Math.ceil(Math.sqrt(dx * dx + dz * dz))
          var k = (z + dz) * w + x + dx
          if (d <= m && (distances[k] === undefined || d < distances[k])) distances[k] = d
        }
      }
    }
    return distances
  },

  // Survey every edited column before touching the world. OCEAN_FLOOR supplies real support beneath water.
  // Inside, the template supplies its own ground and air. Outside, keep the natural surface when it is
  // already within a one-block-per-step slope, including foliage on those untouched columns.
  terrain(level, hm, f, y) {
    var sx = f.size[0], sz = f.size[2], m = this.margin, w = sx + 2 * m
    var low = TtlBuilds.decode(f.fill, sx * sz)
    var distances = this.distances(low, f)
    var floor = Java.loadClass('net.minecraft.world.level.levelgen.Heightmap$Types').OCEAN_FLOOR
    var work = []
    for (var k = 0; k < distances.length; k++) {
      var d = distances[k]
      if (d === undefined) continue
      var bx = k % w - m, bz = Math.floor(k / w) - m
      var x = bx - 14, z = bz - 14
      var natural = hm.ground(x, z)
      if (natural === null) throw new Error(`void beneath the grounds at ${x} ${z}`)
      var ground = Math.min(natural, level.getHeight(floor, x, z))
      if (ground <= hm.minY) throw new Error(`no solid foundation at ${x} ${z}`)
      // A projecting eave or limb can be the only authored block over natural ground.
      var lower = d ? y - d : Math.min(y, y - 7 + low[bz * sx + bx])
      var upper = y + d
      if (d && ground >= lower && natural <= upper) continue
      var top = hm.top(x, z)
      if (ground < lower) {
        work.push([x,z,ground,lower - 1,'minecraft:dirt'])
        if (d) work.push([x,z,lower - 1,lower - 1,'minecraft:grass_block'])
      }
      if (top !== null && top > upper) {
        work.push([x,z,upper,top - 1,'minecraft:air'])
        if (d && ground >= upper) work.push([x,z,upper - 1,upper - 1,'minecraft:grass_block'])
      }
    }
    return work
  },

  earth(server, level, col) {
    var x = col[0], z = col[1], lo = col[2], hi = col[3], id = col[4]
    if (this.run(server, `fill ${x} ${lo} ${z} ${x} ${hi} ${z} ${id}`) > 0) return
    // Vanilla reports failure for an already-correct fill, including on a retry.
    for (var y = lo; y <= hi; y++) {
      if (String(level.getBlock(x, y, z).id) !== id) throw new Error(`could not grade ${x} ${y} ${z}`)
    }
  },

  signs(server, base) {
    var signs = [
      [6,14,['Wayfarer’s Rest','Traveller board','','/ttl guide']],
      [8,14,['One mortal life','Take your time','','']],
      [17,22,['','North road','','']], [18,23,['','East road','','']],
      [17,24,['','South road','','']], [16,23,['','West road','','']]
    ]
    signs.forEach(sign => {
      var pos = `${sign[0] - 14} ${base + 9} ${sign[1] - 14}`
      var msgs = sign[2].map(line => JSON.stringify(JSON.stringify({text: line}))).join(',')
      var nbt = `{is_waxed:1b,front_text:{messages:[${msgs}]}}`
      if (!this.run(server, `execute if block ${pos} minecraft:oak_wall_sign run data merge block ${pos} ${nbt}`) &&
          !this.run(server, `execute if block ${pos} minecraft:oak_wall_sign if data block ${pos} ${nbt}`)) {
        throw new Error(`could not letter sign at ${pos}`)
      }
    })
  },

  place(server) {
    var f = TtlMortalSpawnFootprint
    if (f.size.join(',') !== '39,22,39' || f.margin !== 0) throw new Error('unexpected mortal spawn footprint')
    var level = server.getLevel(TtlLife.MORTAL)
    this.chunks(level)
    var id = Java.loadClass('net.minecraft.resources.ResourceLocation').parse('ttl:mortal_spawn')
    if (!level.getStructureManager().get(id).isPresent()) throw new Error('missing template ttl:mortal_spawn')
    var hm = TtlBuilds.heightmaps(server, {name: 'mortal spawn', dimension: TtlLife.MORTAL, x: 0, z: 0})
    if (!hm) throw new Error('mortal heightmaps unavailable')
    var data = server.persistentData
    var y = data.contains('ttl.mortal.y') ? data.getInt('ttl.mortal.y') : hm.ground(0, 0)
    if (y === null || y - 7 < hm.minY || y - 7 + f.size[1] > level.getMaxBuildHeight()) {
      throw new Error('plaza outside the buildable world')
    }
    var work = this.terrain(level, hm, f, y)
    data.putInt('ttl.mortal.y', y)  // A retry keeps this height even after partial earthworks.
    work.forEach(col => this.earth(server, level, col))
    if (!this.run(server, `place template ttl:mortal_spawn -14 ${y - 7} -14`)) throw new Error('template placement failed')
    this.signs(server, y - 7)
    if (!this.run(server, `execute if block 0 ${y} 5 minecraft:air if block 0 ${y + 1} 5 minecraft:air unless block 0 ${y - 1} 5 minecraft:air`)) {
      throw new Error('arrival ground or headroom missing')
    }
    data.putString('ttl.mortal.spawn', `0.5 ${y} 5.5`)
    data.putInt('ttl.mortal.version', TTL_MORTAL_SPAWN_VERSION)
    console.info(`[ttl] mortal spawn placed at y ${y} (version ${TTL_MORTAL_SPAWN_VERSION})`)
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  server.scheduleInTicks(40, () => {
    if (server.persistentData.getInt('ttl.mortal.version') === TTL_MORTAL_SPAWN_VERSION) return
    try {
      TtlMortalSpawn.place(server)
    } catch (e) {
      console.error(`[ttl] mortal spawn placement failed: ${e}`)
    }
  })
})

BlockEvents.broken(event => {
  if (TtlMortalSpawn.protectedBlock(event.player, event.block)) event.cancel()
})

BlockEvents.placed(event => {
  if (TtlMortalSpawn.protectedBlock(event.entity, event.block)) event.cancel()
})

BlockEvents.rightClicked(event => {
  if (!TtlMortalSpawn.protectedBlock(event.player, event.block)) return
  var id = String(event.item.id)
  if (String(event.block.id) === 'minecraft:barrel' ||
      /(_axe|_hoe|_shovel|bucket)$/.test(id) ||
      ['minecraft:shears', 'minecraft:bone_meal', 'minecraft:flint_and_steel', 'minecraft:fire_charge'].indexOf(id) >= 0) {
    event.cancel()
  }
})
