// Offline tests for the faction argument of TtlRep.add/set (rep/rep.js) and the merit code that feeds it
// (economy/merit.js, economy/guild.js regionOf): merit once passed the faction TABLE that TtlRep.factionAt returns where
// the faction ID belongs, and the staging log said "[ttl] rep: unknown faction [object Object] (reason: merit)" while no
// reputation was granted (20/11/2026). The real rep.js, merit.js and generated data run on a fake player and server.
// Run: node tests/rep_faction.js (tests/test_rep_faction.py runs it with the other unit tests).
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const TTL = path.join(__dirname, '..', 'pack', 'kubejs', 'server_scripts', 'ttl')
const logs = { warn: [], error: [] }

class Data { // persistentData of a player or the server
  constructor () { this.m = {} }
  getString (k) { return k in this.m ? this.m[k] : '' }
  putString (k, v) { this.m[k] = String(v) }
  getBoolean () { return false }
  remove (k) { delete this.m[k] }
}
const player = (name) => ({ username: name, persistentData: new Data(), stages: { has: () => false, add () {}, remove () {} }, tell () {}, getX: () => 1820.5, getZ: () => 1000.5 })
const server = { persistentData: new Data(), getScoreboard: () => ({ getObjective: () => ({}) }), runCommandSilent () { return 0 } }

const ctx = vm.createContext({
  console: { info () {}, log () {}, warn: (m) => logs.warn.push(String(m)), error: (m) => logs.error.push(String(m)) },
  ServerEvents: { loaded () {}, commandRegistry () {} },
  PlayerEvents: { loggedIn () {} },
  BlockEvents: { placed () {} },
  Text: { gold: (s) => s },
  TtlLife: { OVERWORLD: 'minecraft:overworld', phase: () => 'life2', dimensionOf: () => 'minecraft:overworld', uuid: (p) => `uuid-${p.username}` },
  TtlEcon: { weekKey: () => '2026-W47' },
  TtlGuild: { requireLife2 () {} }
})
for (const f of ['generated/data.js', 'rep/rep.js', 'economy/merit.js']) {
  vm.runInContext(fs.readFileSync(path.join(TTL, f), 'utf8'), ctx, { filename: f })
}
const Rep = vm.runInContext('TtlRep', ctx)
const Merit = vm.runInContext('TtlMerit', ctx)
const Data_ = vm.runInContext('TtlData', ctx)
// The canon grid is Java (a chunk map); every block column of this test lies in region J = tempest.
Rep.regionAt = () => 'J'
Rep.sync = () => {} // scoreboards, stages and the renown mirror need a live server
const j = Data_.factions.faction.find(f => f.region === 'J')
assert.ok(j && j.id === 'tempest', 'factions.toml: region J is tempest')

let n = 0
const test = (name, fn) => {
  logs.warn.length = 0; logs.error.length = 0
  try { fn() } catch (e) { e.message = `${name}: ${e.message}`; throw e }
  n++
}
const fresh = () => { const p = player('TtlBotRep'); Rep.set(server, p, 'tempest', 0, 'test setup'); logs.warn.length = 0; return p }
const quiet = () => assert.equal(logs.error.length + logs.warn.length, 0, `${logs.warn} ${logs.error}`)

test('a faction id string still works', () => {
  const p = fresh()
  assert.equal(Rep.add(server, p, 'tempest', 3, 'test'), 3)
  assert.equal(Rep.get(p, 'tempest'), 3)
  quiet()
})

test('an unknown id string keeps the old warning and grants nothing', () => {
  const p = fresh()
  assert.equal(Rep.add(server, p, 'nowhere', 3, 'test'), null)
  assert.match(logs.warn[0], /unknown faction nowhere \(reason: test\)/)
})

test('a faction table is reduced to its id (what TtlRep.factionAt returns)', () => {
  const p = fresh()
  assert.equal(Rep.add(server, p, Rep.factionAt(1, 1), 4, 'merit'), 4)
  assert.equal(Rep.get(p, 'tempest'), 4)
  assert.equal(Rep.set(server, p, j, 7, 'test'), 7)
  assert.equal(Rep.get(p, 'tempest'), 7)
  quiet()
})

test('a { faction } record is reduced to its faction', () => {
  const p = fresh()
  assert.equal(Rep.add(server, p, { faction: 'tempest', amount: 2 }, 2, 'test'), 2)
  assert.equal(Rep.add(server, p, { faction: { id: 'tempest' } }, 1, 'test'), 3)
  assert.equal(Rep.get(p, 'tempest'), 3)
})

test('anything else logs a clear error with the reason and grants nothing', () => {
  for (const bad of [{}, { amount: 5 }, null, undefined, '', '[object Object]', { faction: {} }]) {
    const p = fresh()
    logs.error.length = 0
    assert.equal(Rep.add(server, p, bad, 5, 'merit'), null, `add ${JSON.stringify(bad)}`)
    assert.equal(Rep.set(server, p, bad, 5, 'merit'), null, `set ${JSON.stringify(bad)}`)
    assert.equal(Rep.get(p, 'tempest'), 0)
    assert.equal(logs.error.length, 2)
    assert.match(logs.error[0], /not a faction id.*\(reason: merit\)/)
  }
  assert.equal(Rep.idOf({ amount: 5 }, 'x'), null)
})

// --- merit: mark a Public Works chunk, earn 100 merit; the faction table must not reach TtlRep
const meritBlocks = Data_.economy.merit.blocks.map(String)
const earn = (p, count) => { let g = 0; for (let i = 0; i < count; i++) g += Merit.place(server, p, meritBlocks[0], 1820, 1000); return g }
const worksKey = Merit.chunkKey('minecraft:overworld', 1820, 1000)

test('Merit.faction returns the faction id, not the table', () => {
  assert.equal(Merit.faction(1820, 1000), 'tempest')
  Rep.regionAt = () => null
  assert.equal(Merit.faction(1820, 1000), '')
  Rep.regionAt = () => 'J'
})

test('100 merit in a marked chunk grants reputation with the region faction', () => {
  server.persistentData.remove(Merit.WORKS)
  const p = fresh()
  const r = Merit.mark(server, p)
  assert.equal(r.faction, 'tempest')
  assert.equal(JSON.parse(server.persistentData.getString(Merit.WORKS))[r.key].faction, 'tempest')
  assert.equal(earn(p, 99), 99)
  assert.equal(Rep.get(p, 'tempest'), 0, 'no reputation before the 100th merit')
  assert.equal(earn(p, 1), 1)
  assert.equal(Rep.get(p, 'tempest'), Number(Data_.economy.merit.rep_per_100), 'reputation changed')
  quiet()
})

test('a Public Works record from before the fix (the whole faction table stored) still pays', () => {
  const p = fresh()
  server.persistentData.putString(Merit.WORKS, JSON.stringify({ [worksKey]: { by: 'uuid-TtlBotRep', faction: j } }))
  assert.equal(earn(p, 100), 100)
  assert.equal(Rep.get(p, 'tempest'), 1)
  // ... and so does a record whose faction was lost on the way ("[object Object]" or "")
  for (const lost of ['[object Object]', '']) {
    const q = fresh()
    server.persistentData.putString(Merit.WORKS, JSON.stringify({ [worksKey]: { by: 'uuid-TtlBotRep', faction: lost } }))
    assert.equal(earn(q, 100), 100)
    assert.equal(Rep.get(q, 'tempest'), 1, `faction ${JSON.stringify(lost)}`)
  }
  quiet()
})

test('a chunk outside every faction region pays no reputation and logs nothing', () => {
  Rep.regionAt = () => null
  const p = fresh()
  server.persistentData.putString(Merit.WORKS, JSON.stringify({ [worksKey]: { by: 'uuid-TtlBotRep', faction: '' } }))
  assert.equal(earn(p, 100), 100)
  assert.equal(Rep.get(p, 'tempest'), 0)
  quiet()
  Rep.regionAt = () => 'J'
})

// --- a helper that hands TtlRep.factionAt's table on as if it were an id invites the same bug
test('no script returns a TtlRep.factionAt result unconverted', () => {
  const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)])
  const bad = []
  for (const f of walk(TTL).filter(x => x.endsWith('.js'))) {
    fs.readFileSync(f, 'utf8').split('\n').forEach((line, i) => {
      if (/^\s*return\s+(typeof TtlRep !== 'undefined' \? )?TtlRep\.factionAt\(/.test(line)) bad.push(`${path.relative(TTL, f)}:${i + 1}: ${line.trim()}`)
    })
  }
  assert.deepEqual(bad, [], 'a function that returns the faction table (not its id) invites this bug again')
})

console.log(`rep_faction: ${n} tests passed`)
