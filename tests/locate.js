// life/locate.js without a game: every anchor of the generated table resolves (at its anchor, and at the placement the
// placers recorded), unanchored builds and landmarks join once placed, and players' directions are rounded and never
// carry coordinates. The command wiring itself is tests/ingame/locate.rcon.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const ttl = path.join(__dirname, '../pack/kubejs/server_scripts/ttl')
const store = new Map()
const server = { persistentData: { getString: k => store.get(k) || '' } }
const builds = [
  { name: 'blumund', title: 'Blumund - Londo', dimension: 'minecraft:overworld' },
  { name: 'mortal_market', title: 'The Folk Market', dimension: 'ttl:mortal_realm' },
  { name: 'test_hut', title: 'Test hut', dimension: 'ttl:spirit_corridor' }
]
const landmarks = [{ name: 'goblin_village', title: 'Old goblin village' }, { name: 'lone_ruin', title: 'Lone ruin' }]
const sandbox = {
  ServerEvents: { commandRegistry: fn => { sandbox.registry = fn } },
  TtlBuilds: { all: () => builds, find: n => builds.find(b => b.name === n), str: (s, b, k) => s.persistentData.getString(`ttl.build.${b.name}.${k}`) },
  TtlLandmarks: { all: () => landmarks, find: n => landmarks.find(l => l.name === n), key: (l, k) => `ttl.landmark.${l.name}.${k}` },
  console
}
vm.createContext(sandbox)
vm.runInContext(fs.readFileSync(path.join(ttl, 'generated/anchors.js'), 'utf8') + '\nthis.TtlAnchors = TtlAnchors', sandbox)
vm.runInContext(fs.readFileSync(path.join(ttl, 'life/locate.js'), 'utf8') + '\nthis.TtlLocate = TtlLocate', sandbox)
const L = sandbox.TtlLocate
const anchors = sandbox.TtlAnchors
const ids = Object.keys(anchors)
assert(ids.length >= 58, `only ${ids.length} anchors`)

// Nothing placed: every anchor id resolves to its own anchor, none of the unanchored ones is listed.
assert.deepEqual([...L.ids(server)], ids.slice().sort())
for (const id of ids) {
  const r = L.resolve(server, id)
  assert(r, `${id} does not resolve`)
  assert.equal(r.placed, false, id)
  assert.deepEqual([r.x, r.z], [anchors[id].x, anchors[id].z], id)
  assert(r.title && r.title.length > 0, `${id} has no title`)
  assert.equal(r.dim, 'minecraft:overworld')
}
assert.equal(L.resolve(server, 'tempest').title, 'Tempest')
assert.equal(L.resolve(server, 'dwargon').title, 'Dwargon')
assert.equal(L.resolve(server, 'nowhere'), null)
assert.equal(L.resolve(server, 'mortal_market'), null)

// Recorded placements win (Tempest's arrival is stored with .5), at their own position.
store.set('ttl.tempest.arrival', '1720.5 69 900.5')
store.set('ttl.dwargon.gate', '1878.5 120 -540.5')
store.set('ttl.build.blumund.at', '-433 70 160')
store.set('ttl.landmark.goblin_village.at', '1500 64 700')
const at = id => { const r = L.resolve(server, id); return [r.placed, r.x, r.y, r.z] }
assert.deepEqual(at('tempest'), [true, 1720, 69, 900])
assert.deepEqual(at('dwargon'), [true, 1878, 120, -541])
assert.deepEqual(at('blumund'), [true, -433, 70, 160])
assert.deepEqual(at('goblin_village'), [true, 1500, 64, 700])
assert.equal(L.resolve(server, 'ballachia').placed, false)

// Builds and landmarks without an anchor of their own appear once they have a placement, in their dimension.
store.set('ttl.build.mortal_market.at', '10 70 -20')
store.set('ttl.landmark.lone_ruin.at', '5 70 5')
assert.deepEqual([...L.ids(server)], ids.concat(['mortal_market', 'lone_ruin']).sort())
const m = L.resolve(server, 'mortal_market')
assert.deepEqual([m.dim, m.placed, m.x, m.z], ['ttl:mortal_realm', true, 10, -20])
assert.equal(L.resolve(server, 'test_hut'), null)

// Players: map places only, no spots, no arrival.
const pids = L.playerIds()
assert(pids.includes('tempest') && pids.includes('dwargon') && pids.includes('lake_siss'))
for (const id of ['arrival', 'shizu_spawn', 'old_well', 'rookie_camp', 'dwargon_throne', 'kaijin_smithy']) assert(!pids.includes(id), id)

// Directions: +X east, +Z south; Tempest is south of the arrival, Dwargon north of it.
assert.equal(L.COMPASS_EN[L.sector(0, -100)], 'north')
assert.equal(L.COMPASS_EN[L.sector(100, 0)], 'east')
assert.equal(L.COMPASS_EN[L.sector(0, 100)], 'south')
assert.equal(L.COMPASS_EN[L.sector(-100, 0)], 'west')
assert.equal(L.COMPASS_EN[L.sector(100, 100)], 'south-east')
assert.equal(L.COMPASS_EN[L.sector(-100, -100)], 'north-west')
const [en, nl] = L.bearing('Tempest', 1660, -100, { x: 1720, z: 900 })
assert.equal(en, 'Tempest lies about 1,000 blocks south of you.')
assert.equal(nl, 'Tempest ligt ongeveer 1.000 blokken ten zuiden van je.')
assert.equal(L.bearing('X', 0, 0, { x: 800, z: 800 })[0], 'X lies about 1,100 blocks south-east of you.')
assert.equal(L.bearing('X', 0, 0, { x: -420, z: 0 })[0], 'X lies about 400 blocks west of you.')
assert.match(L.bearing('X', 0, 0, { x: 30, z: 40 })[0], /very close/)
for (const s of [en, nl, L.bearing('X', 0, 0, { x: 1234, z: -4321 })[1]]) assert(!/-?\d{4}, ~|\[/.test(s), s)
console.log('locate ok')
