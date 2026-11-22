// Offline test for the Life 1 status presets (design/data/karma.toml [presets], karma/life1_status.js, issue #75): each
// preset, judged by the real karma formula (karma/karma.js TtlKarma.judge on the generated data), gives the tier and the
// Dark flag it promises; and applying a preset through TtlLife1Status sets exactly its stats after zeroing the others.
// Run: node tests/life1_status.js (tests/test_life1_status.py runs it).
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const TTL = path.join(__dirname, '..', 'pack', 'kubejs', 'server_scripts', 'ttl')
const ctx = vm.createContext({
  console: { info () {}, warn () {}, error: (...a) => console.error(...a), log: console.log },
  ServerEvents: { commandRegistry () {} },
  PlayerEvents: { loggedIn () {} }
})
for (const f of ['generated/data.js', 'karma/karma.js', 'karma/life1_status.js']) {
  vm.runInContext(fs.readFileSync(path.join(TTL, f), 'utf8'), ctx, { filename: f })
}
const K = vm.runInContext('TtlKarma', ctx)
const L = vm.runInContext('TtlLife1Status', ctx)
const presets = L.presets()

assert.equal(Object.keys(presets).sort().join(','), 'dark,elite,legendary,normal,underdog')
for (const t of K.tiers()) assert.ok(presets[t.id], `a preset for every tier (${t.id})`)

// 1. Every preset is judged as its tier (and Dark only where it says so).
for (const name of Object.keys(presets)) {
  const p = presets[name]
  const v = K.judge(Object.assign({}, p.stats), null)
  assert.equal(v.tier, p.tier, `preset ${name}: tier ${v.tier}, score ${v.score}, days ${v.days}`)
  assert.equal(v.dark, !!p.dark, `preset ${name}: dark ${v.dark}`)
}

// 2. Applying: the soul must be in Life 1; every preset stat is zeroed first, then the preset's own are set.
{
  const set = []
  vm.runInContext('TtlLife = { phase: p => p.phase }', ctx)
  K.set = (server, player, key, n) => set.push([key, n])
  K.current = () => ({ tier: 'elite', dark: false })
  const player = { username: 'TtlBotL1', phase: 'life1', persistentData: { putString (k, v) { this[k] = v } } }
  L.apply({}, player, 'elite', 'Yasuke')
  // JSON round trip: arrays made inside the vm context are not deepEqual to this realm's.
  const plain = x => JSON.parse(JSON.stringify(x))
  const zeroed = plain(L.presetStats())
  assert.deepEqual(plain(set.slice(0, zeroed.length)), zeroed.map(k => [k, 0]))
  assert.deepEqual(plain(set.slice(zeroed.length)), Object.entries(plain(presets.elite.stats)))
  assert.equal(JSON.parse(player.persistentData['ttl.l1.staffset']).preset, 'elite')
  assert.equal(JSON.parse(player.persistentData['ttl.l1.staffset']).by, 'Yasuke')
  assert.throws(() => L.apply({}, Object.assign({}, player, { phase: 'life2' }), 'elite', 'Yasuke'), /not in Life 1/)
  assert.throws(() => L.apply({}, player, 'godlike', 'Yasuke'), /unknown preset/)
  K.current = () => ({ tier: 'normal', dark: false })
  assert.throws(() => L.apply({}, player, 'elite', 'Yasuke'), /out of date/)
}

// 3. The staff stamp goes with the other karma keys at the next Life 1 start.
assert.ok(K.KEYS.includes('ttl.l1.staffset'))

console.log('life1_status: all checks passed')
