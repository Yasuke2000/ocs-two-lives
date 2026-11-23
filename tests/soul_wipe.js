// Offline tests for the soul wipe (life/soul_wipe.js, issues #72 #73): a full reset takes every ability (uniques only
// through the registry, never by a direct Tensura command) and resets the body to Human; the Life 1 death strip takes
// the non-unique abilities and leaves uniques and the body alone. Run: node tests/soul_wipe.js (tests/test_soul_wipe.py).
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const TTL = path.join(__dirname, '..', 'pack', 'kubejs', 'server_scripts', 'ttl')

function world (abilities, opts) {
  opts = opts || {}
  const log = { cmds: [], registry: [], human: 0 }
  const state = { list: abilities.slice(), down: !!opts.down }
  const ctx = vm.createContext({
    console: { info () {}, warn () {}, error () {}, log: console.log },
    ServerEvents: { commandRegistry () {} },
    TtlLife: { makeHuman () { log.human++ } },
    TtlManas: { learned: () => (state.down ? null : state.list.map(s => ({ id: s.id, unique: s.unique, mastery: s.mastery === undefined ? 0 : s.mastery }))) },
    TtlCmd: {
      run (server, cmd) {
        log.cmds.push(cmd)
        const m = /^tensura edit ability revoke (\S+) (\S+)$/.exec(cmd)
        // Tensura puts a forgotten resistance back to the start of learning instead of removing it.
        if (m) state.list = state.list.flatMap(s => s.id !== m[2] ? [s] : (/_resistance$/.test(s.id) ? [{ id: s.id, unique: false, mastery: -500 }] : []))
        return 1
      },
      attempt (server, cmd) {
        log.cmds.push(cmd)
        return { result: opts.resetFails ? 0 : 1, error: opts.resetFails ? 'refused' : '' }
      }
    },
    TtlRegistry: {
      revoke (server, player, id, reason) {
        log.registry.push(['revoke', id, reason])
        state.list = state.list.filter(s => s.id !== id)
      },
      revokeAll (server, player, reason) {
        log.registry.push(['revokeAll', reason])
        state.list = state.list.filter(s => !s.unique)
      }
    },
    Java: { loadClass () { throw new Error('no Java here') } }
  })
  vm.runInContext(fs.readFileSync(path.join(TTL, 'life/soul_wipe.js'), 'utf8'), ctx, { filename: 'soul_wipe.js' })
  return { W: vm.runInContext('TtlSoulWipe', ctx), log, state }
}

const PLAYER = { username: 'TtlBotWipe' }
const SLIME = [
  { id: 'tensura:predator', unique: true },
  { id: 'tensura:telepathy', unique: false }, // common skill
  { id: 'tensura:cold_resistance', unique: false }, // resistance
  { id: 'tensura:magic_sense', unique: false }, // extra skill
  { id: 'tensura:absorb_dissolve', unique: false } // a Slime intrinsic
]
const directRevokes = log => log.cmds.filter(c => c.startsWith('tensura edit ability revoke')).map(c => c.split(' ').pop())

// 1. A full reset: uniques through the registry, every other ability revoked, the body reset to a fresh Human.
{
  const { W, log, state } = world(SLIME)
  const line = W.full({}, PLAYER, 'character reset')
  assert.equal(state.list.filter(s => (s.mastery ?? 0) >= 0).length, 0, 'no ability is held')
  assert.deepEqual(state.list.map(s => s.id), ['tensura:cold_resistance'], 'only the resistance, back at the start of learning')
  assert.deepEqual(log.registry[0], ['revokeAll', 'character reset'])
  assert.deepEqual(directRevokes(log).sort(), ['tensura:absorb_dissolve', 'tensura:cold_resistance', 'tensura:magic_sense', 'tensura:telepathy'])
  assert.ok(!directRevokes(log).includes('tensura:predator'), 'a unique is never revoked behind the registry')
  const cancel = log.cmds.indexOf('ttlrebirth cancel TtlBotWipe')
  const reset = log.cmds.indexOf('tensura reset TtlBotWipe race tensura:human')
  assert.ok(cancel >= 0 && reset > cancel, 'an open rebirth menu is closed before the race reset')
  assert.ok(reset > log.cmds.lastIndexOf('tensura edit ability revoke TtlBotWipe tensura:telepathy'), 'the body is reset after the revokes')
  assert.equal(log.human, 0, 'no fallback race set when Tensura took the reset')
  assert.match(line, /4 other abilities revoked, body reset to a fresh Human/)
}

// 2. The ability pass never touches a unique, even one still listed (the registry's revokes land a moment later).
{
  const { W, log, state } = world(SLIME)
  const res = W.abilities({}, PLAYER)
  assert.equal(res.uniques, 1)
  assert.equal(log.registry.length, 0)
  assert.ok(!directRevokes(log).includes('tensura:predator'))
  assert.ok(state.list.some(s => s.id === 'tensura:predator'))
}

// 2b. Tensura never forgets a resistance: it goes back to the start of learning (negative mastery), which is not held.
{
  const { W, state } = world([{ id: 'tensura:cold_resistance', unique: false, mastery: 0 }])
  const realRun = W.abilities
  state.list = [{ id: 'tensura:cold_resistance', unique: false, mastery: -500 }]
  assert.equal(W.held(state.list[0]), false)
  assert.equal(W.held({ id: 'x', mastery: 0 }), true)
  assert.equal(realRun.call(W, {}, PLAYER).left.length, 0)
}

// 3. The Life 1 death strip: non-uniques taken, a unique left to the registry, the body and race untouched.
{
  const { W, log, state } = world(SLIME)
  W.lifeOne({}, PLAYER)
  assert.deepEqual(state.list.filter(s => (s.mastery ?? 0) >= 0).map(s => s.id), ['tensura:predator'])
  assert.equal(log.registry.length, 0, 'the registry is not touched at a Life 1 death')
  assert.ok(!log.cmds.some(c => c.startsWith('tensura reset')), 'no race reset at a Life 1 death')
}

// 4. ManasCore unreadable: nothing is revoked blindly, the body is still reset; a refused reset falls back to the race.
{
  const { W, log } = world(SLIME, { down: true })
  const line = W.full({}, PLAYER, 'character reset')
  assert.equal(directRevokes(log).length, 0)
  assert.match(line, /not readable/)
  const r = world(SLIME, { resetFails: true })
  assert.match(r.W.full({}, PLAYER), /NOT reset/)
  assert.equal(r.log.human, 1, 'Tensura refused the reset: at least the race is set to Human')
}

console.log('soul_wipe: all checks passed')
