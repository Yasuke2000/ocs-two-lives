// Offline tests for the terrain repair planner (pack/kubejs/server_scripts/ttl/life/repair.js) through the spec
// that life/builds.js hands it (TtlBuilds.repairSpec): synthetic worlds (a height field plus single blocks), the plan
// applied to the world by a small `fill` interpreter, then the blocks checked. Run: node tests/build_repair.js
// (tests/test_build_repair.py runs it with the other unit tests).
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const LIFE = path.join(__dirname, '..', 'pack', 'kubejs', 'server_scripts', 'ttl', 'life')
const ctx = vm.createContext({
  console: { info() {}, warn() {}, error: (...a) => console.error(...a), log: console.log },
  ServerEvents: { loaded() {}, commandRegistry() {} },
  TtlData: { builds: [] }
})
vm.runInContext(fs.readFileSync(path.join(LIFE, 'repair.js'), 'utf8'), ctx)
vm.runInContext(fs.readFileSync(path.join(LIFE, 'builds.js'), 'utf8'), ctx)
const TtlRepair = vm.runInContext('TtlRepair', ctx)
const TtlBuilds = vm.runInContext('TtlBuilds', ctx)

const NONE = -999
const MAT = { top: 'minecraft:grass_block', fill: 'minecraft:dirt', deep: 'minecraft:stone' }

function rle (values) {
  const out = []
  for (const v of values) {
    if (out.length && out[out.length - 2] === v) out[out.length - 1]++
    else out.push(v, 1)
  }
  return out
}

// A world: height(x, z) = y of the top terrain block (grass, 3 dirt, stone below) or null (void); single blocks on top.
function makeWorld (height) {
  const cells = new Map()
  const k = (x, y, z) => `${x},${y},${z}`
  const w = {
    minY: -64,
    reads: 0,
    natural (x, y, z) {
      const h = height(x, z)
      if (h === null || y > h || y < -64) return 'minecraft:air'
      return y === h ? 'minecraft:grass_block' : y >= h - 3 ? 'minecraft:dirt' : 'minecraft:stone'
    },
    peek (x, y, z) {
      const v = cells.get(k(x, y, z))
      return v === undefined ? w.natural(x, y, z) : v
    },
    id (x, y, z) {
      w.reads++
      return w.peek(x, y, z)
    },
    set (x, y, z, id) { cells.set(k(x, y, z), id) },
    box (x1, y1, z1, x2, y2, z2, id) {
      for (let x = x1; x <= x2; x++) for (let y = y1; y <= y2; y++) for (let z = z1; z <= z2; z++) w.set(x, y, z, id)
    },
    // MOTION_BLOCKING_NO_LEAVES: solid blocks, fluids and logs; plants, fire and air do not count.
    top (x, z) {
      for (let y = 200; y >= -64; y--) {
        const id = w.peek(x, y, z)
        const c = TtlRepair.cls(id)
        if (c === 'solid' || c === 'water' || c === 'lava' || id.endsWith('_log')) return y + 1
      }
      return -64
    },
    loaded: () => true,
    // `fill x1 y1 z1 x2 y2 z2 block [replace filter]`, as the game would run it.
    apply (cmd) {
      const m = cmd.match(/^fill (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (\S+)(?: replace (\S+))?$/)
      assert.ok(m, `not a fill: ${cmd}`)
      const [x1, y1, z1, x2, y2, z2] = m.slice(1, 7).map(Number)
      assert.ok(x1 <= x2 && y1 <= y2 && z1 <= z2, cmd)
      assert.ok((x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1) <= 32768, `fill over 32768 blocks: ${cmd}`)
      const only = m[8] === '#minecraft:fire' ? ['minecraft:fire', 'minecraft:soul_fire'] : m[8] ? [m[8]] : null
      for (let x = x1; x <= x2; x++) {
        for (let y = y1; y <= y2; y++) {
          for (let z = z1; z <= z2; z++) {
            if (!only || only.includes(w.id(x, y, z))) w.set(x, y, z, m[7])
          }
        }
      }
    }
  }
  return w
}

// A build like design/builds/*.toml: box sx x sz at corner (0, base, 0), ground layer g, bottom(bx, bz) = lowest
// defined layer or null (undefined column); defined columns get a stone brick floor from their bottom up to g and
// walls 3 high on the box edge, so the test can check the repair never touches them.
function place (world, o) {
  const sx = o.sx
  const sz = o.sz
  const bottoms = []
  for (let bz = 0; bz < sz; bz++) {
    for (let bx = 0; bx < sx; bx++) {
      const v = o.bottom ? o.bottom(bx, bz) : 0
      bottoms.push(v === null ? NONE : v)
      if (v === null) continue
      for (let y = v; y <= o.g; y++) world.set(bx, o.base + y, bz, o.floor ? o.floor(bx, bz, y) : 'minecraft:stone_bricks')
      for (let y = o.g + 1; y <= o.g + 3; y++) world.set(bx, o.base + y, bz, bx === 0 || bz === 0 || bx === sx - 1 || bz === sz - 1 ? 'minecraft:oak_planks' : 'minecraft:air')
    }
  }
  const f = { size: [sx, o.g + 4, sz], none: NONE, fill: rle(bottoms), bottom: rle(bottoms) }
  const b = { name: o.name || 'synthetic', dimension: 'minecraft:overworld', anchor: [1, o.g + 1, 1], repair: o.repair !== false,
    repair_margin: o.ring === undefined ? 8 : o.ring, repair_depth: o.depth || 48, repair_keep_water: !!o.keepWater }
  const geo = { x0: 0, z0: 0, base: o.base }
  return { f, b, geo, spec: TtlBuilds.repairSpec(b, f, geo, MAT) }
}

// Plan, check that no command touches a defined cell, apply.
function repair (world, built) {
  const before = new Map()
  const { f, geo } = built
  for (let bz = 0; bz < f.size[2]; bz++) {
    for (let bx = 0; bx < f.size[0]; bx++) {
      for (let y = 0; y < f.size[1]; y++) before.set(`${bx},${y},${bz}`, world.id(bx, geo.base + y, bz))
    }
  }
  const res = TtlRepair.planAll(built.spec, world)
  res.cmds.forEach(c => world.apply(c))
  // Cells at or above a defined column's bottom are the build's: unchanged.
  const bottom = TtlBuilds.decode(f.bottom, f.size[0] * f.size[2])
  for (let bz = 0; bz < f.size[2]; bz++) {
    for (let bx = 0; bx < f.size[0]; bx++) {
      const v = bottom[bz * f.size[0] + bx]
      if (v === NONE) continue
      for (let y = v; y < f.size[1]; y++) {
        assert.equal(world.id(bx, geo.base + y, bz), before.get(`${bx},${y},${bz}`), `build cell ${bx} ${geo.base + y} ${bz} changed`)
      }
    }
  }
  return res
}

const kind = (world, x, y, z) => TtlRepair.cls(world.id(x, y, z))
const tests = []
const test = (name, fn) => tests.push([name, fn])

test('cave and lava under the box are filled down to ground, a cave beyond the ring is not', () => {
  const world = makeWorld(() => 64)
  world.box(2, 50, 2, 6, 60, 6, 'minecraft:cave_air') // closed cave under the box, 3 blocks under the floor
  world.set(4, 50, 4, 'minecraft:lava')
  world.box(30, 50, 30, 33, 55, 33, 'minecraft:cave_air') // far outside
  const built = place(world, { sx: 9, sz: 9, base: 64, g: 0, ring: 6 })
  const res = repair(world, built)
  for (let y = 50; y <= 60; y++) assert.equal(kind(world, 4, y, 4), 'solid', `cave cell 4 ${y} 4`)
  assert.equal(world.id(4, 50, 4), 'minecraft:stone')
  assert.equal(world.id(4, 61, 4), 'minecraft:dirt') // the 3 cells under the build: dirt, like the fit
  assert.equal(res.foundation, 5 * 5 * 11 - 1)
  assert.equal(res.lava, 1)
  assert.equal(res.skirt, 0)
  assert.equal(world.id(31, 52, 31), 'minecraft:cave_air')
})

test('a ravine under the box edge and across the ring: filled under the box, to the rim in the ring, open beyond', () => {
  // A 2-wide ravine along x at z 3..4, from x -12 to the box edge, 24 deep; under the box it runs on 3 columns
  // as a cave below a 3-block roof (the overhang the fit cannot see).
  const world = makeWorld(() => 64)
  world.box(-12, 40, 3, -1, 64, 4, 'minecraft:air')
  world.box(0, 40, 3, 2, 60, 4, 'minecraft:cave_air')
  const built = place(world, { sx: 9, sz: 9, base: 65, g: 0, ring: 6 })
  const res = repair(world, built)
  for (let y = 40; y <= 64; y++) assert.equal(kind(world, 1, y, 3), 'solid', `under the box at y ${y}`)
  for (let x = -6; x <= -1; x++) {
    assert.equal(world.id(x, 64, 3), 'minecraft:grass_block', `ring column ${x} surface`)
    for (let y = 40; y < 64; y++) assert.equal(kind(world, x, y, 4), 'solid', `ring column ${x} at y ${y}`)
  }
  assert.equal(world.id(-10, 50, 3), 'minecraft:air') // the ravine beyond the ring stays
  assert.equal(res.foundation, 3 * 2 * 21) // the cave under the box; its roof is natural ground
  assert.ok(res.skirt >= 6 * 2 * 25)
})

test('a crevice under an overhang in the ring is closed, a deep pit is filled to its rim', () => {
  const world = makeWorld(() => 70)
  world.box(-3, 60, 1, -3, 68, 3, 'minecraft:air') // a slit under a 2-block lip at d 3
  world.box(13, 40, 2, 14, 70, 3, 'minecraft:air') // a 2x2 pit at d 4..5, 30 deep, open to the sky
  const built = place(world, { sx: 9, sz: 9, base: 70, g: 0, ring: 8 })
  repair(world, built)
  for (let y = 60; y <= 68; y++) assert.equal(kind(world, -3, y, 2), 'solid', `slit cell y ${y}`)
  assert.equal(world.id(13, 70, 2), 'minecraft:grass_block')
  assert.equal(world.id(14, 69, 3), 'minecraft:dirt')
  assert.equal(world.id(14, 45, 3), 'minecraft:stone')
})

test('lava and fire in the ring: a pool is filled, lava above the ground layer and fire become air, beyond is kept', () => {
  const world = makeWorld((x, z) => x >= 14 ? 70 : 64)
  world.box(11, 63, 2, 13, 64, 4, 'minecraft:lava') // pool at d 3..5, flush with the ground
  world.set(15, 71, 6, 'minecraft:lava') // a lava cell on the hill above the ground layer (d 7)
  world.set(-2, 65, 4, 'minecraft:fire')
  world.box(30, 63, 2, 31, 64, 3, 'minecraft:lava') // a pool beyond the ring
  const built = place(world, { sx: 9, sz: 9, base: 64, g: 0, ring: 8 })
  const res = repair(world, built)
  assert.equal(world.id(12, 64, 3), 'minecraft:grass_block')
  assert.equal(world.id(12, 63, 3), 'minecraft:dirt')
  assert.equal(world.id(15, 71, 6), 'minecraft:air')
  assert.equal(world.id(-2, 65, 4), 'minecraft:air')
  assert.equal(world.id(30, 64, 2), 'minecraft:lava')
  assert.equal(res.lava, 3 * 3 * 2 + 1 + 1)
})

test('undefined box columns: ditch filled to the ground layer, path continued, bare rock covered, no deeper', () => {
  // Ground layer at y 66 (g 2, base 64). Columns bx 0..1 are undefined; the terrain there is a ditch (y 62) at
  // bz 0..4 and a rock bank (y 70, cut back to 66 by the fit) at bz 5..8. Defined row bz 2 has a dirt path.
  const world = makeWorld((x, z) => x >= 0 && x <= 1 && z >= 0 && z <= 4 ? 62 : 66)
  world.box(0, 67, 5, 1, 70, 8, 'minecraft:air') // what the fit's clear left: bare stone at 66
  world.box(0, 66, 5, 1, 66, 8, 'minecraft:stone')
  const built = place(world, {
    sx: 9, sz: 9, base: 64, g: 2, ring: 4,
    bottom: (bx, bz) => bx <= 1 ? null : 0,
    floor: (bx, bz, y) => y === 2 ? (bz === 2 ? 'minecraft:dirt_path' : 'minecraft:grass_block') : 'minecraft:dirt'
  })
  const res = repair(world, built)
  assert.equal(world.id(1, 66, 2), 'minecraft:dirt_path') // nearest defined neighbour (2, 2) holds a path
  assert.equal(world.id(0, 66, 2), 'minecraft:dirt_path') // two columns away still the path
  assert.equal(world.id(1, 66, 0), 'minecraft:grass_block')
  assert.equal(world.id(1, 65, 0), 'minecraft:dirt')
  assert.equal(world.id(1, 63, 0), 'minecraft:dirt')
  assert.equal(world.id(0, 66, 6), 'minecraft:grass_block') // bare rock in the sky's view
  assert.equal(world.id(0, 67, 6), 'minecraft:air') // never above the ground layer
  assert.ok(res.foundation >= 2 * 5 * 4 + 2 * 4)
})

test('water: touching the box is banked up to its surface, a pond and a kept-water site are left alone', () => {
  const lake = (x, z) => x >= 9 // a lake east of the box, from the box edge out
  const height = (x, z) => lake(x, z) ? 58 : 64
  const wet = world => {
    for (let x = 9; x <= 30; x++) for (let z = -10; z <= 20; z++) world.box(x, 59, z, x, 63, z, 'minecraft:water')
    world.box(-6, 59, 0, -5, 63, 1, 'minecraft:water') // a pond at d 5..6, open to the sky, not touching the box
    world.box(-6, 64, 0, -5, 64, 1, 'minecraft:air')
  }
  let world = makeWorld(height)
  wet(world)
  let built = place(world, { sx: 9, sz: 9, base: 64, g: 0, ring: 6 })
  let res = repair(world, built)
  for (let x = 9; x <= 14; x++) assert.equal(kind(world, x, 63, 4), 'solid', `bank at x ${x}`)
  assert.equal(world.id(9, 63, 4), 'minecraft:grass_block')
  assert.equal(world.id(15, 63, 4), 'minecraft:water') // the lake beyond the ring
  assert.equal(world.id(-6, 63, 0), 'minecraft:water') // the pond
  assert.ok(res.skirt > 0)

  world = makeWorld(height)
  wet(world)
  built = place(world, { sx: 9, sz: 9, base: 64, g: 0, ring: 6, keepWater: true })
  res = repair(world, built)
  for (let x = 9; x <= 20; x++) assert.equal(world.id(x, 63, 4), 'minecraft:water', `kept lake at x ${x}`)
  assert.equal(world.id(-6, 63, 0), 'minecraft:water')
})

test('void: a build floating over nothing, and a floating island, are left alone', () => {
  let world = makeWorld(() => null)
  let built = place(world, { sx: 5, sz: 5, base: 64, g: 0, ring: 8 })
  let res = repair(world, built)
  assert.equal(res.cmds.length, 0)
  // An island 4 thick under the box, void below it and round it: only the island's own cave is filled.
  world = makeWorld((x, z) => x >= -2 && x <= 6 && z >= -2 && z <= 6 ? 63 : null)
  world.box(-2, -64, -2, 6, 59, 6, 'minecraft:air') // island = 60..63
  world.set(2, 61, 2, 'minecraft:cave_air')
  built = place(world, { sx: 5, sz: 5, base: 64, g: 0, ring: 8 })
  res = repair(world, built)
  assert.equal(world.id(2, 61, 2), 'minecraft:dirt')
  assert.equal(world.id(2, 59, 2), 'minecraft:air')
  assert.equal(res.foundation, 1)
  assert.equal(res.deep, 0)
})

test('a cave that runs on below repair_depth is closed down to the depth when there is ground below', () => {
  const world = makeWorld(() => 64)
  world.box(2, 20, 2, 4, 60, 4, 'minecraft:cave_air')
  const built = place(world, { sx: 7, sz: 7, base: 65, g: 0, ring: 2, depth: 16 })
  const res = repair(world, built)
  assert.equal(kind(world, 3, 49, 3), 'solid')
  assert.equal(world.id(3, 48, 3), 'minecraft:cave_air')
  assert.equal(res.deep, 9)
})

test('deep in the ground the scan reads every other cell and still finds every cave 2 or more high', () => {
  for (let top = 20; top <= 40; top++) {
    const world = makeWorld(() => 64)
    world.box(3, top - 1, 3, 3, top, 3, 'minecraft:cave_air') // 2 high, at every parity
    const built = place(world, { sx: 7, sz: 7, base: 65, g: 0, ring: 0 })
    const res = repair(world, built)
    assert.equal(res.foundation, 2, `cave at ${top - 1}..${top}`)
    assert.equal(kind(world, 3, top, 3), 'solid')
  }
})

test('fills merge into few commands, each at most 32768 blocks, and repair = false plans nothing', () => {
  const world = makeWorld(() => 64)
  world.box(0, 20, 0, 59, 60, 59, 'minecraft:cave_air') // a 60 x 60 x 41 hall under the box
  let built = place(world, { sx: 60, sz: 60, base: 65, g: 0, ring: 2 })
  const res = repair(world, built)
  assert.ok(res.cmds.length <= 12, `${res.cmds.length} commands`)
  assert.equal(kind(world, 30, 20, 30), 'solid')
  const off = place(makeWorld(() => 64), { sx: 5, sz: 5, base: 65, g: 0, repair: false })
  assert.equal(off.spec.enabled, false)
})

test('gentle natural terrain round the box is left as it is; only real pits are filled', () => {
  // Rolling ground +-2 round a box set 1 above its highest point: the fit's slope is switched off here, so whatever the
  // ring gets comes from the pit rule alone.
  const world = makeWorld((x, z) => 64 + Math.round(2 * Math.sin(x / 7) * Math.cos(z / 9)))
  const built = place(world, { sx: 40, sz: 40, base: 67, g: 0, ring: 8 })
  const col = built.spec.col
  built.spec.col = (gx, gz) => {
    const c = col(gx, gz)
    if (c && c.t === 'ring') c.slope = null
    return c
  }
  assert.equal(repair(world, built).skirt, 0)
  const pitted = makeWorld((x, z) => 64 + Math.round(2 * Math.sin(x / 7) * Math.cos(z / 9)))
  pitted.box(-4, 50, 10, -3, 70, 11, 'minecraft:air')
  const again = place(pitted, { sx: 40, sz: 40, base: 67, g: 0, ring: 8 })
  again.spec.col = built.spec.col
  const res = repair(pitted, again)
  assert.ok(res.skirt > 0 && kind(pitted, -4, 55, 10) === 'solid')
})

test('tests/ingame/build_repair.rcon offline: the fit (builds.js terrainCommands) then the repair, same checks', () => {
  // test_hut: corner 2498 63 -2, 5 x 6 x 5, floor layer 0 (ground y 63), margin 8, repair ring 8; void round the patch.
  const patch = (x, z) => x >= 2484 && x <= 2516 && z >= -14 && z <= 14
  const world = makeWorld(() => null)
  world.natural = (x, y, z) => patch(x, z) && y >= 50 && y <= 62 ? (y === 62 ? 'minecraft:grass_block' : 'minecraft:stone') : 'minecraft:air'
  const rcon = text => text.trim().split('\n').forEach(line => {
    const m = line.trim().match(/^(fill|setblock) (.*)$/)
    const a = m[2].split(' ')
    if (m[1] === 'setblock') world.set(+a[0], +a[1], +a[2], a[3])
    else world.box(+a[0], +a[1], +a[2], +a[3], +a[4], +a[5], a[6])
  })
  rcon(`fill 2499 55 -1 2501 60 1 minecraft:cave_air
    setblock 2500 55 0 minecraft:lava
    fill 2496 56 -3 2497 62 3 minecraft:air
    fill 2498 58 -1 2498 61 1 minecraft:air
    fill 2505 61 -1 2507 62 1 minecraft:lava
    fill 2499 59 -4 2501 61 -3 minecraft:water
    fill 2492 59 -1 2493 61 1 minecraft:cave_air
    fill 2499 51 6 2500 62 7 minecraft:air
    setblock 2494 63 4 minecraft:fire
    fill 2512 60 0 2513 62 1 minecraft:water`)
  // The hut as it stands from earlier placements: floor y 63, walls, roof y 67, explicit air on y 68.
  world.box(2498, 63, -2, 2502, 63, 2, 'minecraft:stone_bricks')
  world.box(2498, 64, -2, 2502, 66, 2, 'minecraft:oak_planks')
  world.box(2499, 64, -1, 2501, 66, 1, 'minecraft:air')
  world.box(2500, 64, 2, 2500, 65, 2, 'minecraft:air')
  world.box(2498, 67, -2, 2502, 67, 2, 'minecraft:spruce_planks')
  const b = { name: 'test_hut', dimension: 'ttl:spirit_corridor', anchor: [2, 1, 2], margin: 8, clear_above: true, repair: true,
    repair_depth: 48, repair_margin: 8, repair_keep_water: false }
  const f = { size: [5, 6, 5], none: NONE, fill: [0, 25], top: [5, 25], bottom: [0, 25] }
  const geo = { x0: 2498, z0: -2, base: 63 }
  // builds.js heightmaps(), on the synthetic world (MOTION_BLOCKING and _NO_LEAVES are the same here).
  const hm = {
    top: (x, z) => world.top(x, z) <= -64 ? null : world.top(x, z),
    ground: (x, z) => {
      let y = world.top(x, z)
      if (y <= -64) return null
      for (let n = 0; n < 40 && y > -63; n++) {
        const id = world.peek(x, y - 1, z)
        if (id !== 'minecraft:air' && !TtlBuilds.NOT_GROUND.some(k => id.indexOf(k) >= 0)) break
        y--
      }
      return y
    },
    floor: (x, z) => {
      let y = hm.ground(x, z)
      if (y === null) return null
      for (let n = 0; n < 64 && TtlBuilds.WET.includes(world.peek(x, y - 1, z)); n++) y--
      return y
    }
  }
  TtlBuilds.terrainCommands(b, f, hm, geo, MAT).forEach(c => world.apply(c))
  const res = TtlRepair.planAll(TtlBuilds.repairSpec(b, f, geo, MAT), world)
  res.cmds.forEach(c => world.apply(c))
  assert.ok(res.foundation >= 40 && res.skirt >= 20 && res.lava >= 18, `${res.foundation} ${res.skirt} ${res.lava}`)
  const solid = [[2500, 58, 0], [2500, 55, 0], [2498, 59, 0], [2498, 61, 1], [2497, 57, 0], [2506, 61, 0], [2500, 60, -3],
    [2501, 59, -4], [2492, 60, 0], [2500, 60, 7]]
  solid.forEach(([x, y, z]) => assert.equal(kind(world, x, y, z), 'solid', `${x} ${y} ${z}`))
  assert.equal(world.id(2506, 62, 0), 'minecraft:grass_block')
  assert.equal(world.id(2507, 62, 1), 'minecraft:grass_block')
  assert.equal(world.id(2499, 62, 6), 'minecraft:grass_block')
  assert.equal(world.id(2494, 63, 4), 'minecraft:air')
  assert.equal(world.id(2512, 62, 0), 'minecraft:water')
  assert.equal(world.id(2500, 63, 0), 'minecraft:stone_bricks')
  assert.equal(world.id(2500, 64, 2), 'minecraft:air')
})

test('the planner yields to the time budget and still ends with the same plan', () => {
  const mk = () => {
    const world = makeWorld(() => 64)
    world.box(2, 50, 2, 6, 60, 6, 'minecraft:cave_air')
    world.box(-3, 55, 0, -2, 64, 8, 'minecraft:air')
    return world
  }
  const a = mk()
  const whole = TtlRepair.planAll(place(a, { sx: 9, sz: 9, base: 65, g: 0, ring: 6 }).spec, a)
  const b = mk()
  const p = TtlRepair.planner(place(b, { sx: 9, sz: 9, base: 65, g: 0, ring: 6 }).spec, b)
  let calls = 0
  while (!p.step(() => true)) calls++
  assert.ok(calls > 10, `${calls} slices`)
  assert.deepEqual(p.result.cmds, whole.cmds)
})

let failed = 0
for (const [name, fn] of tests) {
  try {
    fn()
    console.log(`ok   ${name}`)
  } catch (e) {
    failed++
    console.log(`FAIL ${name}\n     ${e.message}`)
  }
}
if (failed) process.exit(1)
