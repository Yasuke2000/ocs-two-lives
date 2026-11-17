// Places the Armed Nation of Dwargon (blueprints/dwargon.py → structure ttl:dwargon) in the Tensura world, in
// the southern mountains of Dwargon on the canon map (pack/config/ttl/canon_map.txt), its gate facing Jura and
// world spawn. Bump TTL_DWARGON_VERSION after changing the blueprint; a world reset of the overworld places it
// again on the new terrain (world_reset.js).
const TTL_DWARGON_VERSION = 1

const TtlDwargon = {
  // The arrival point in front of the gate; the blueprint's arrival is (56, 4, 104) and it is 112 x 124 wide.
  GATE: { x: 160, z: -900 },
  ARRIVAL: [56, 4, 104],
  SIZE: [112, 76, 124],
  PROBE: 'ttl_dwargon_probe',

  run(server, cmd) {
    server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} run ${cmd}`)
  },

  box() {
    var x0 = this.GATE.x - this.ARRIVAL[0]
    var z0 = this.GATE.z - this.ARRIVAL[2]
    return { x0: x0, z0: z0, x1: x0 + this.SIZE[0], z1: z0 + this.SIZE[2] }
  },

  surfaceY(server) {
    server.runCommandSilent(`execute in ${TtlLife.OVERWORLD} positioned ${this.GATE.x} 0 ${this.GATE.z} positioned over motion_blocking_no_leaves run summon minecraft:marker ~ ~ ~ {Tags:["${this.PROBE}"]}`)
    var y = null
    var probe = this.PROBE
    server.getLevel(TtlLife.OVERWORLD).getEntities().forEach(e => {
      if (e.getTags().contains(probe)) y = Math.floor(e.getY())
    })
    this.run(server, `kill @e[type=minecraft:marker,tag=${probe}]`)
    return y
  },

  place(server) {
    var y = this.surfaceY(server)
    if (y === null) {
      console.warn('[ttl] dwargon: no surface found at the gate; not placed')
      return false
    }
    var b = this.box()
    // The arrival point (blueprint y 4) stands on the measured surface.
    var base = y - this.ARRIVAL[1]
    this.run(server, `place template ttl:dwargon ${b.x0} ${base} ${b.z0}`)
    server.persistentData.putInt('ttl.dwargon.version', TTL_DWARGON_VERSION)
    server.persistentData.putString('ttl.dwargon.gate', `${this.GATE.x + 0.5} ${y} ${this.GATE.z + 0.5}`)
    console.info(`[ttl] dwargon placed: corner ${b.x0} ${base} ${b.z0}, gate at ${this.GATE.x} ${y} ${this.GATE.z} (version ${TTL_DWARGON_VERSION})`)
    return true
  },

  // forceload generates the 8 x 8 chunks first; mountains take a while, so placement waits 10 s.
  schedule(server) {
    var b = this.box()
    var self = this
    this.run(server, `forceload add ${b.x0} ${b.z0} ${b.x1} ${b.z1}`)
    server.scheduleInTicks(200, () => {
      try {
        self.place(server)
      } catch (e) {
        console.error(`[ttl] dwargon placement failed: ${e}`)
      }
      self.run(server, `forceload remove ${b.x0} ${b.z0} ${b.x1} ${b.z1}`)
    })
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  if (server.persistentData.getInt('ttl.dwargon.version') === TTL_DWARGON_VERSION) return
  TtlDwargon.schedule(server)
})
