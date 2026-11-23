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

// A soul's persistentData, as far as these scripts use it.
const soul = (phase, extra) => {
  const d = Object.assign({}, extra || {})
  return {
    username: 'TtlBotL1',
    phase,
    persistentData: {
      d,
      putString (k, v) { d[k] = v },
      getString (k) { return d[k] === undefined ? '' : String(d[k]) },
      putBoolean (k, v) { d[k] = !!v },
      getBoolean (k) { return !!d[k] }
    }
  }
}
// JSON round trip: arrays made inside the vm context are not deepEqual to this realm's.
const plain = x => JSON.parse(JSON.stringify(x))

// 2. Applying: the soul must be in Life 1; every preset stat is zeroed first, then the preset's own are set; each use is
// stamped on the soul (the last 10).
{
  const set = []
  vm.runInContext('TtlLife = { phase: p => p.phase }', ctx)
  const realCurrent = K.current
  const realSet = K.set
  K.set = (server, player, key, n) => set.push([key, n])
  K.current = () => ({ tier: 'elite', dark: false })
  const player = soul('life1')
  L.apply({}, player, 'elite', 'Yasuke')
  const zeroed = plain(L.presetStats())
  assert.deepEqual(plain(set.slice(0, zeroed.length)), zeroed.map(k => [k, 0]))
  assert.deepEqual(plain(set.slice(zeroed.length)), Object.entries(plain(presets.elite.stats)))
  L.days({}, player, 30, 'Ereh')
  const stamps = plain(L.stamps(player))
  assert.deepEqual(stamps.map(x => [x.what, x.by]), [['elite', 'Yasuke'], ['days 30', 'Ereh']])
  assert.deepEqual(plain(set[set.length - 1]), ['play_time', 30 * vm.runInContext('TtlData.karma.ticks_per_day', ctx)])
  for (let i = 0; i < 12; i++) L.stamp(player, 'x', `n${i}`)
  assert.equal(L.stamps(player).length, 10, 'the stamp keeps the last 10')
  // An old single-object stamp (before the list) is still read.
  assert.equal(plain(L.stamps(soul('life1', { 'ttl.l1.staffset': '{"by":"Y","preset":"dark","at":1}' })))[0].what, 'dark')
  assert.throws(() => L.apply({}, soul('life2'), 'elite', 'Yasuke'), /not in Life 1/)
  assert.throws(() => L.days({}, soul('corridor'), 30, 'Yasuke'), /not in Life 1/)
  assert.throws(() => L.apply({}, player, 'godlike', 'Yasuke'), /unknown preset/)
  K.current = () => ({ tier: 'normal', dark: false })
  assert.throws(() => L.apply({}, player, 'elite', 'Yasuke'), /out of date/)
  K.current = realCurrent
  K.set = realSet
}

// 3. The gates: what each higher tier still needs (Ereh's case: a Hero with 12 of the Legend's 30 active days, no boss).
{
  const g = plain(L.gates({ tier: 'elite', score: 700, days: 12, bosses: 0 }))
  assert.equal(g.length, 1)
  assert.equal(g[0].tier, 'legendary')
  assert.deepEqual(g[0].missing, ['score 700/1000', 'active days 12/30', 'major bosses 0/1'])
  const all = plain(L.gates({ tier: 'underdog', score: 5000, days: 99, bosses: 3 }))
  assert.deepEqual(all.map(x => x.tier), ['normal', 'elite', 'legendary'])
  assert.ok(all.every(x => x.missing.length === 0))
  assert.equal(L.gates({ tier: 'legendary', score: 0, days: 0, bosses: 0 }).length, 0)
}

// 4. The Trial result: only in the Corridor after the Last Wish; a running Trial is ended with that result.
{
  const finished = []
  vm.runInContext('TtlTrial = { finish: (s, p, wish, passed, why) => TtlTrialCalls.push([wish, passed, why]) }', ctx)
  ctx.TtlTrialCalls = finished
  const waiting = soul('corridor', { 'ttl.step': 'race', 'ttl.wish': 'strength' })
  L.trial({}, waiting, true, 'Yasuke')
  assert.equal(waiting.persistentData.getBoolean('ttl.trial.done'), true)
  assert.equal(waiting.persistentData.getBoolean('ttl.trial.passed'), true)
  assert.throws(() => L.trial({}, waiting, false, 'Yasuke'), /Trial done/)
  const running = soul('corridor', { 'ttl.step': 'trial', 'ttl.wish': 'knowledge' })
  L.trial({}, running, false, 'Yasuke')
  assert.deepEqual(plain(finished), [['knowledge', false, 'set by Yasuke']])
  assert.throws(() => L.trial({}, soul('corridor', { 'ttl.step': 'wish' }), true, 'Yasuke'), /after the Last Wish/)
  assert.throws(() => L.trial({}, soul('life1'), true, 'Yasuke'), /not in the Spirit Corridor/)
}

// 5. The staff stamp goes with the other karma keys at the next Life 1 start; every subcommand is op only.
assert.ok(K.KEYS.includes('ttl.l1.staffset'))
{
  const src = fs.readFileSync(path.join(TTL, 'karma/life1_status.js'), 'utf8')
  const tree = src.slice(src.indexOf("Commands.literal('life1')"))
  assert.match(tree.slice(0, 120), /\.requires\(src => src\.hasPermission\(2\)\)/, '/ttl life1 is op only (the whole subtree)')
}

console.log('life1_status: all checks passed')
