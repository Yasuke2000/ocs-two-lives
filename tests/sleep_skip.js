// Offline tests for sleeping through the night outside the overworld (life/sleep.js, issue #86): the night slept away in
// the Mortal Realm moves the overworld's clock (the one every dimension reads) to the event's morning and ends the rain;
// the overworld's own sleep is vanilla's and left alone; a second listener (after a /reload) changes nothing.
// Run: node tests/sleep_skip.js (tests/test_sleep.py runs it).
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const TTL = path.join(__dirname, '..', 'pack', 'kubejs', 'server_scripts', 'ttl')
const handlers = []
const ran = []
const GameRules = { RULE_WEATHER_CYCLE: 'doWeatherCycle' }
const ctx = vm.createContext({
  console: { info () {}, warn () {}, error: (...a) => console.error(...a), log: console.log },
  ServerEvents: { loaded (fn) { fn({ server: { runCommandSilent: c => ran.push(c) } }) }, commandRegistry () {} },
  NativeEvents: { onEvent (cls, fn) { handlers.push([cls, fn]) } },
  TtlLife: { OVERWORLD: 'minecraft:overworld' },
  Java: {
    loadClass (name) {
      if (name === 'net.neoforged.neoforge.event.level.SleepFinishedTimeEvent') return 'SleepFinishedTimeEvent'
      if (name === 'net.minecraft.world.level.GameRules') return GameRules
      throw new Error(`unexpected class ${name}`)
    }
  }
})
vm.runInContext(fs.readFileSync(path.join(TTL, 'life/sleep.js'), 'utf8'), ctx, { filename: 'sleep.js' })
const S = vm.runInContext('TtlSleep', ctx)

assert.equal(handlers.length, 1)
assert.equal(handlers[0][0], 'SleepFinishedTimeEvent', 'listens to NeoForge SleepFinishedTimeEvent')
assert.equal(S.hooked, true)
assert.deepEqual(ran, ['gamerule playersSleepingPercentage 50'], 'vanilla percentage rule, 50 %')

function overworld (time, raining, weatherCycle) {
  return {
    t: time,
    raining,
    weather: null,
    getDayTime () { return this.t },
    setDayTime (t) { this.t = t },
    isRaining () { return this.raining },
    setWeatherParameters (a, b, rain, thunder) { this.weather = [a, b, rain, thunder]; this.raining = rain },
    getGameRules: () => ({ getBoolean: rule => rule === 'doWeatherCycle' && weatherCycle })
  }
}
const fire = (dim, ow, newTime) => {
  const level = { dimension: dim, getServer: () => ({ overworld: () => ow }) }
  handlers.forEach(h => h[1]({ getLevel: () => level, getNewTime: () => newTime }))
}

// Mortal Realm: night at 18000 of day 3 -> the next morning (day 4, time 0), rain ended.
{
  const ow = overworld(3 * 24000 + 18000, true, true)
  fire('ttl:mortal_realm', ow, 4 * 24000)
  assert.equal(ow.t, 4 * 24000)
  assert.equal(S.timeOfDay({ overworld: () => ow }), 0)
  assert.deepEqual(ow.weather, [0, 0, false, false])
}
// doWeatherCycle off: the rain stays.
{
  const ow = overworld(18000, true, false)
  fire('ttl:mortal_realm', ow, 24000)
  assert.equal(ow.t, 24000)
  assert.equal(ow.weather, null)
}
// The overworld's own sleep: vanilla already set the time, nothing to do here.
{
  const ow = overworld(18000, false, true)
  fire('minecraft:overworld', ow, 24000)
  assert.equal(ow.t, 18000)
}
// Never back in time (a stale event, or a second listener after the first moved the clock).
{
  const ow = overworld(24000 + 100, false, true)
  fire('ttl:mortal_realm', ow, 24000)
  assert.equal(ow.t, 24000 + 100)
}

console.log('sleep_skip: all checks passed')
