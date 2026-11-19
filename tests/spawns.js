// Offline tests for the graded spawn zones (life/mortal_spawns.js TtlSpawnZones, design/data/spawns.toml) on the real
// generated data: no hostile spawn in Tempest's town radius, hostile_keep of them in the reduced band, a cap on animals,
// and nothing but natural spawns touched. Run: node tests/spawns.js (tests/test_spawns.py runs it).
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const TTL = path.join(__dirname, '..', 'pack', 'kubejs', 'server_scripts', 'ttl')
let near = []
class AABB { constructor (...a) { this.a = a } }
const ctx = vm.createContext({
  console: { info () {}, warn () {}, error: (...a) => console.error(...a), log: console.log },
  ServerEvents: { loaded () {}, commandRegistry () {} },
  EntityEvents: { spawned () {}, checkSpawn () {} },
  TtlLife: { OVERWORLD: 'minecraft:overworld', isMortal: () => false },
  TtlBoss: { byEntity: id => (id === 'tensura:orc_disaster' ? {} : null) },
  Java: { loadClass: () => AABB }
})
for (const f of ['generated/data.js', 'generated/anchors.js', 'life/mortal_spawns.js']) {
  vm.runInContext(fs.readFileSync(path.join(TTL, f), 'utf8'), ctx, { filename: f })
}
const Z = vm.runInContext('TtlSpawnZones', ctx)
const SAFE = vm.runInContext('TtlSafeSpawns', ctx)
const T = vm.runInContext('TtlAnchors.tempest', ctx)
const conf = vm.runInContext('TtlData.spawns.zone.tempest', ctx)
const level = {
  dimension: 'minecraft:overworld',
  getMinBuildHeight: () => -64,
  getMaxBuildHeight: () => 320,
  getEntitiesWithin: () => near
}
const mob = (dx, kind, type) => ({
  level,
  type: type || (kind === 'monster' ? 'tensura:direwolf' : 'minecraft:pig'),
  getX: () => T.x + dx,
  getZ: () => T.z,
  isMonster: () => kind === 'monster',
  isAnimal: () => kind === 'animal',
  isAlive: () => true
})
let n = 0
const test = (name, fn) => { near = []; fn(); n++ }

test('the data: town 150, reduced band to 400 at 25 %', () => {
  assert.equal(conf.anchor, 'tempest')
  assert.ok(conf.town_radius >= 150 && conf.reduced_radius >= 400, JSON.stringify(conf))
  assert.ok(conf.hostile_keep > 0 && conf.hostile_keep <= 0.25)
})

test('no natural hostile spawn in the town, hostile_keep in the band, all beyond', () => {
  assert.equal(Z.refuse(mob(100, 'monster'), 'NATURAL', 0.99), true)
  assert.equal(Z.refuse(mob(conf.town_radius, 'monster'), 'CHUNK_GENERATION', 0.99), true)
  assert.equal(Z.refuse(mob(300, 'monster'), 'NATURAL', conf.hostile_keep - 0.01), false, 'a roll under keep spawns')
  assert.equal(Z.refuse(mob(300, 'monster'), 'NATURAL', conf.hostile_keep), true, 'a roll at or over keep is refused')
  assert.equal(Z.refuse(mob(conf.reduced_radius + 10, 'monster'), 'NATURAL', 0.99), false)
  let kept = 0
  for (let i = 0; i < 1000; i++) if (!Z.refuse(mob(300, 'monster'), 'NATURAL', i / 1000)) kept++
  assert.equal(kept, Math.round(conf.hostile_keep * 1000))
})

test('summons, spawners, events, breeding and bosses are never refused', () => {
  for (const t of ['COMMAND', 'SPAWNER', 'EVENT', 'BREEDING', 'MOB_SUMMONED', 'SPAWN_EGG', 'TRIGGERED', 'TRIAL_SPAWNER']) {
    assert.equal(Z.refuse(mob(10, 'monster'), t, 0.99), false, t)
  }
  assert.equal(Z.refuse(mob(10, 'monster', 'tensura:orc_disaster'), 'NATURAL', 0.99), false, 'a boss keeps bosses/boss.js rule')
})

test('animals are capped per square, never refused below the cap', () => {
  near = []
  for (let i = 0; i < conf.passive_cap - 1; i++) near.push(mob(0, 'animal'))
  near.push(mob(0, 'monster'))
  assert.equal(Z.refuse(mob(50, 'animal'), 'CHUNK_GENERATION'), false)
  near.push(mob(0, 'animal'))
  assert.equal(Z.refuse(mob(50, 'animal'), 'CHUNK_GENERATION'), true)
  assert.equal(Z.refuse(mob(conf.passive_radius + 10, 'animal'), 'NATURAL'), false, 'beyond passive_radius')
  assert.equal(Z.refuse(mob(50, 'animal'), 'BREEDING'), false)
})

test('the bands', () => {
  assert.equal(Z.band('minecraft:overworld', T.x + 10, T.z), 'none')
  assert.equal(Z.band('minecraft:overworld', T.x, T.z + 250), 'reduced')
  assert.equal(Z.band('minecraft:overworld', T.x + 500, T.z), 'open')
  assert.equal(Z.band('ttl:mortal_realm', T.x, T.z), 'open')
})

test('the hard hostile-free squares (and so the magicule shelter) are unchanged', () => {
  const t = SAFE.ZONES.find(s => s.id === 'tempest')
  assert.equal(t.radius, 56)
})

console.log(`spawns: ${n} tests passed`)
