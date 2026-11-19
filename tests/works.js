// Offline tests for the world works (pack/kubejs/server_scripts/ttl/life/works.js, forests.js, trade_roads.js) on the
// real generated/placements.js: the JS geometry against the planner's (tools/lerfing/*.py, through a JSON file that
// tests/test_works.py writes), and the per-column / per-tree commands on synthetic terrain.
// Run: node tests/works.js [expected.json] (tests/test_works.py runs it with the other unit tests).
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const TTL = path.join(__dirname, '..', 'pack', 'kubejs', 'server_scripts', 'ttl')
const ctx = vm.createContext({
  console: { info () {}, warn () {}, error: (...a) => console.error(...a), log: console.log },
  ServerEvents: { loaded () {}, commandRegistry () {} },
  TtlLife: { OVERWORLD: 'minecraft:overworld' },
  // life/state.js: the command's result through the dispatcher (KubeJS 2101's runCommandSilent returns nothing)
  TtlCmd: { run: (server, c) => server.dispatch(c), attempt: (server, c) => ({ result: server.dispatch(c), error: '' }) }
})
for (const f of ['generated/placements.js', 'life/works.js', 'life/forests.js', 'life/trade_roads.js']) {
  vm.runInContext(fs.readFileSync(path.join(TTL, f), 'utf8'), ctx, { filename: f })
}
const W = vm.runInContext('TtlWorks', ctx)
const F = vm.runInContext('TtlForests', ctx)
const R = vm.runInContext('TtlTradeRoads', ctx)
const D = vm.runInContext('TtlPlacementData', ctx)
let n = 0
const test = (name, fn) => { fn(); n++ }

test('both kinds are registered and every work has data', () => {
  assert.deepEqual(Object.keys(W.kinds()), ['road', 'forest'])
  assert.ok(Object.keys(D.forests).length >= 2)
  assert.ok(D.roads.tempest_dwargon)
})

// --- against the Python planner
const want = process.argv[2] ? JSON.parse(fs.readFileSync(process.argv[2], 'utf8')) : null
if (want) {
  test('road columns equal the planner rasterize()', () => {
    for (const [id, exp] of Object.entries(want.roads)) {
      const cols = R.columns(D.roads[id])
      const got = Object.keys(cols).sort()
      assert.equal(got.length, exp.columns.length, `${id}: column count`)
      const set = new Set(got)
      for (const [k, y, i] of exp.columns) {
        assert.ok(set.has(k), `${id}: ${k} missing in JS`)
        assert.equal(cols[k][0], y, `${id}: y at ${k}`)
        assert.equal(cols[k][1], i, `${id}: arc at ${k}`)
      }
      assert.equal(JSON.stringify(R.lanterns(D.roads[id])), JSON.stringify(exp.lanterns), `${id}: lanterns`)
    }
  })
  test('giant boxes equal the planner giant_box()', () => {
    for (const [id, exp] of Object.entries(want.forests)) {
      const p = D.forests[id]
      p.giants.forEach((g, k) => {
        const b = F.giantBox(p.templates[p.giant_keys[g[0]]], g[1], g[2], F.ROT[g[3]])
        assert.deepEqual([b.cx, b.cz, b.x0, b.z0, b.x1, b.z1], exp.boxes[k], `${id}: giant ${k}`)
      })
      for (const ln of exp.lanes) {
        const l = p.lanes[ln.k]
        const seg = F.laneSegment(l.offline, l.side, l.toward, l.length)
        seg.forEach((v, j) => assert.ok(Math.abs(v - ln.seg[j]) < 1e-9, `${id}: lane ${ln.k}`))
      }
    }
  })
}

// --- geometry
test('rotations put the trunk where asked and keep the box size', () => {
  const tp = { size: [39, 41, 42], trunk: [17, 18] }
  for (const rot of F.ROT) {
    const b = F.giantBox(tp, 100, 200, rot)
    const o = F.rotate(rot, 17, 18)
    assert.deepEqual([b.cx + o[0], b.cz + o[1]], [100, 200])
    const w = b.x1 - b.x0 + 1
    const l = b.z1 - b.z0 + 1
    assert.deepEqual(rot === 'clockwise_90' || rot === 'counterclockwise_90' ? [l, w] : [w, l], [39, 42])
  }
})

test('the road is about 2 x half + 1 wide and every centre sample is paved', () => {
  const r = D.roads.tempest_dwargon
  const cols = R.columns(r)
  const samples = R.arcSamples(r.points)
  assert.equal(samples.length, r.profile.length)
  for (const [x, z] of samples) assert.ok(cols[`${Math.floor(x + 0.5)},${Math.floor(z + 0.5)}`], `centre ${x} ${z}`)
  const per = Object.keys(cols).length / samples.length
  assert.ok(per >= 2 * r.half + 0.5 && per <= 2 * r.half + 2.5, `columns per block ${per}`)
})

// --- commands on synthetic terrain
function fakeServer (result = 1) {
  const cmds = []
  const record = c => cmds.push(c.replace(/^execute in \S+ run /, ''))
  // runCommandSilent as in KubeJS 2101: no result
  return { cmds, runCommandSilent (c) { record(c) }, dispatch (c) { record(c); return result } }
}
function fakeHm (ground, opts = {}) {
  return {
    block: (x, y, z) => (opts.block ? opts.block(x, y, z) : 'minecraft:air'),
    ground: (x, z) => ground(x, z),
    floor: (x, z) => (opts.bed ? opts.bed(x, z) : ground(x, z)),
    wet: (x, z) => (opts.wet ? opts.wet(x, z) : false),
    soil: (x, z) => (opts.soil ? opts.soil(x, z) : true),
    top: (x, z) => ground(x, z)
  }
}

test('a road column fills a dip, sets the surface, clears 4 above and gets a slab before a rise', () => {
  const r = { half: 2, profile: [70, 71], bridges: [], stone_from: [], surface: { 'minecraft:dirt_path': 1 }, stone: { 'minecraft:cobblestone': 1 }, bridge: {} }
  const s = fakeServer()
  assert.equal(R.lay(s, fakeHm(() => 66), r, [], 5, 5, [70, 0, 0]), 'road')
  assert.ok(s.cmds.includes('fill 5 66 5 5 66 5 minecraft:stone'), s.cmds.join('\n'))
  assert.ok(s.cmds.includes('fill 5 67 5 5 69 5 minecraft:dirt'))
  assert.ok(s.cmds.includes('fill 5 71 5 5 74 5 minecraft:air'))
  assert.ok(s.cmds.includes('setblock 5 70 5 minecraft:dirt_path'))
  assert.ok(s.cmds.includes('setblock 5 71 5 minecraft:cobblestone_slab[type=bottom]'))
})

test('a road column in a cut clears down to the road, at most CUT above it', () => {
  const r = { half: 2, profile: [70], bridges: [], stone_from: [], surface: { 'minecraft:gravel': 1 }, stone: {}, bridge: {} }
  const s = fakeServer()
  R.lay(s, fakeHm(() => 79), r, [], 0, 0, [70, 0, 0])
  assert.ok(s.cmds.includes('fill 0 71 0 0 78 0 minecraft:air'), s.cmds.join('\n'))
  const s2 = fakeServer()
  R.lay(s2, fakeHm(() => 120), r, [], 0, 0, [70, 0, 0])
  assert.ok(s2.cmds.includes('fill 0 71 0 0 86 0 minecraft:air'), s2.cmds.join('\n'))
})

test('bridge columns get a deck, railings on the edge and pillars every 5 blocks', () => {
  const r = { half: 2, profile: [66, 66, 66, 66, 66, 66], bridges: [[0, 5]], stone_from: [], surface: {}, stone: {}, bridge: { deck: 'minecraft:spruce_planks', railing: 'minecraft:spruce_fence', pillar: 'minecraft:spruce_log' } }
  const s = fakeServer()
  const hm = fakeHm(() => 65, { wet: () => true, bed: () => 60 })
  assert.equal(R.lay(s, hm, r, [], 0, 0, [66, 5, 2]), 'bridge')
  assert.ok(s.cmds.includes('setblock 0 66 0 minecraft:spruce_planks'))
  assert.ok(s.cmds.includes('setblock 0 67 0 minecraft:spruce_fence'))
  assert.ok(s.cmds.includes('fill 0 60 0 0 65 0 minecraft:spruce_log'), s.cmds.join('\n'))
  const mid = fakeServer()
  R.lay(mid, hm, r, [], 0, 1, [66, 3, 0.5])
  assert.ok(!mid.cmds.some(c => c.includes('fence') || c.includes('log')))
})

test('kept columns are left alone', () => {
  const r = { half: 2, profile: [70], bridges: [], stone_from: [], surface: { 'minecraft:gravel': 1 }, stone: {}, bridge: {} }
  const s = fakeServer()
  assert.equal(R.lay(s, fakeHm(() => 70), r, [{ x0: 0, z0: 0, x1: 9, z1: 9 }], 3, 3, [70, 0, 0]), 'kept')
  assert.equal(s.cmds.length, 0)
})

test('a giant is planted with its roots 5 under the lowest ground, never on sand, in a kept box or a lane', () => {
  const p = D.forests.tempest
  const g = p.giants[0]
  const tp = p.templates[p.giant_keys[g[0]]]
  const rules = { kept: [], lanes: [] }
  const s = fakeServer()
  assert.equal(F.giant(s, fakeHm((x, z) => (x === g[1] && z === g[2] ? 70 : 72)), p, rules, g), null)
  const b = F.giantBox(tp, g[1], g[2], F.ROT[g[3]])
  assert.deepEqual(s.cmds, [`place template ${p.giant_keys[g[0]]} ${b.cx} 65 ${b.cz} ${F.ROT[g[3]]}`])
  assert.equal(F.giant(fakeServer(), fakeHm(() => 70, { soil: () => false }), p, rules, g), 'ground')
  assert.equal(F.giant(fakeServer(), fakeHm((x) => (x > g[1] ? 80 : 70)), p, rules, g), 'slope')
  assert.equal(F.giant(fakeServer(), fakeHm(() => 70), p, { kept: [{ x0: b.x1, z0: b.z1, x1: b.x1 + 5, z1: b.z1 + 5 }], lanes: [] }, g), 'kept')
  assert.equal(F.giant(fakeServer(), fakeHm(() => 70), p, { kept: [], lanes: [{ half: 4, seg: [g[1] - 20, g[2], g[1] + 20, g[2]] }] }, g), 'lane')
  assert.equal(F.giant(fakeServer(0), fakeHm(() => 70), p, rules, g), 'place failed')
})

test('a spot whose trunk already stands is left alone (a re-run plants nothing twice)', () => {
  const p = D.forests.tempest
  const g = p.giants[0]
  const u = p.understory[0]
  const trunk = (x0, z0) => (x, y, z) => (x === x0 && z === z0 && y === 70 ? 'minecraft:dark_oak_log' : 'minecraft:air')
  const s = fakeServer()
  assert.equal(F.giant(s, fakeHm(() => 70, { block: trunk(g[1], g[2]) }), p, { kept: [], lanes: [] }, g), 'standing')
  assert.equal(F.understory(s, fakeHm(() => 70, { block: trunk(u[1], u[2]) }), p, { kept: [], lanes: [] }, u), 'standing')
  assert.deepEqual(s.cmds, [])
  assert.equal(JSON.stringify(F.counts('3 4 5')), '[3,4,5,0,0]')
})

test('understory trees go on dry soil only', () => {
  const p = D.forests.treyni
  const u = p.understory[0]
  const s = fakeServer()
  assert.equal(F.understory(s, fakeHm(() => 71), p, { kept: [], lanes: [] }, u), null)
  assert.deepEqual(s.cmds, [`place feature ${p.features[u[0]]} ${u[1]} 71 ${u[2]}`])
  assert.equal(F.understory(fakeServer(), fakeHm(() => 71, { wet: () => true }), p, { kept: [], lanes: [] }, u), 'ground')
  assert.equal(F.understory(fakeServer(0), fakeHm(() => 71), p, { kept: [], lanes: [] }, u), 'no room')
})

test('pieces cover every tree and column exactly once', () => {
  for (const [id, p] of Object.entries(D.forests)) {
    const pcs = F.pieces(p)
    assert.equal(pcs.reduce((t, pc) => t + pc.giants.length, 0), p.giants.length, id)
    assert.equal(pcs.reduce((t, pc) => t + pc.under.length, 0), p.understory.length, id)
    for (const pc of pcs) {
      const a = pc.area
      assert.ok((a.x1 - a.x0) < 16 * 12 && (a.z1 - a.z0) < 16 * 12, `${id}: tile area ${JSON.stringify(a)} too big for one hold`)
    }
  }
  for (const [id, r] of Object.entries(D.roads)) {
    const pcs = R.pieces(r)
    assert.equal(pcs.reduce((t, pc) => t + pc.cols.length, 0), Object.keys(R.columns(r)).length, id)
  }
})

console.log(`works: ${n} tests passed`)
