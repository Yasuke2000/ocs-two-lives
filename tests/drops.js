// Offline tests for life/drops.js (TtlDrops) and the sweep in life/chunk_hold.js on a fake level: a cleared column
// leaves nothing that leaned on it, gravel over a gap turns solid, a container is emptied before it goes, and the sweep
// after a piece removes only the young items away from players and sets falling blocks down where they land.
// Run: node tests/drops.js (tests/test_drops.py runs it with the other unit tests).
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const TTL = path.join(__dirname, '..', 'pack', 'kubejs', 'server_scripts', 'ttl')

// --- a tiny block world
class Block { constructor (id, rule) { this.id = id; this.rule = rule || null } defaultBlockState () { return new State(this) } }
class FallingBlock extends Block {}
FallingBlock.isFree = st => st.isAir()
const blocks = {}
const block = (id, rule, falls) => { blocks[id] = falls ? new FallingBlock(id, rule) : new Block(id, rule); return blocks[id] }
class State {
  constructor (b) { this.b = b }
  getBlock () { return this.b }
  isAir () { return this.b.id === 'minecraft:air' }
  canSurvive (level, pos) { return this.b.rule ? this.b.rule(level, pos) : true }
}
const below = (level, p) => level.at(p.x, p.y - 1, p.z)
block('minecraft:air')
block('minecraft:stone'); block('minecraft:dirt'); block('minecraft:grass_block'); block('minecraft:chest')
block('minecraft:sandstone'); block('minecraft:oak_log')
block('minecraft:gravel', null, true); block('minecraft:sand', null, true)
block('minecraft:short_grass', (l, p) => ['minecraft:grass_block', 'minecraft:dirt'].includes(below(l, p)))
block('minecraft:tall_grass_upper', (l, p) => below(l, p) === 'minecraft:tall_grass_lower')
block('minecraft:tall_grass_lower', (l, p) => below(l, p) === 'minecraft:grass_block')
block('minecraft:moss_carpet', (l, p) => below(l, p) !== 'minecraft:air')
block('minecraft:wall_torch', (l, p) => l.at(p.x + 1, p.y, p.z) !== 'minecraft:air') // on the block east of it
block('minecraft:cave_vines', (l, p) => ['minecraft:cave_vines', 'minecraft:stone'].includes(l.at(p.x, p.y + 1, p.z)))
class BlockPos { constructor (x, y, z) { this.x = x; this.y = y; this.z = z } }
class AABB { constructor (...a) { this.a = a } }
class Entity {
  constructor (x, y, z, age) { this.x = x; this.y = y; this.z = z; this.age = age; this.alive = true }
  getX () { return this.x } getY () { return this.y } getZ () { return this.z }
  getAge () { return this.age } isAlive () { return this.alive } discard () { this.alive = false }
}
class ItemEntity extends Entity {}
class FallingBlockEntity extends Entity {
  constructor (x, y, z, time, id) { super(x, y, z, 0); this.time = time; this.st = new State(blocks[id]) }
  getBlockState () { return this.st }
}
const cleared = []
function fakeLevel () {
  const cells = new Map()
  const k = (x, y, z) => `${x},${y},${z}`
  const level = {
    cells,
    entities: [],
    playersAt: [],
    flags: [],
    at: (x, y, z) => cells.get(k(x, y, z)) || 'minecraft:air',
    put: (x, y, z, id) => cells.set(k(x, y, z), id),
    getBlockState: p => new State(blocks[level.at(p.x, p.y, p.z)]),
    setBlock (p, st, flags) { level.flags.push(flags); level.put(p.x, p.y, p.z, st.b.id); return true },
    getBlockEntity: p => (level.at(p.x, p.y, p.z) === 'minecraft:chest' ? { chestAt: k(p.x, p.y, p.z) } : null),
    getMinBuildHeight: () => -64,
    getMaxBuildHeight: () => 320,
    getEntitiesWithin: () => level.entities
  }
  return level
}
const J = {
  'net.minecraft.world.level.block.Blocks': { AIR: { defaultBlockState: () => new State(blocks['minecraft:air']) }, DIRT: { defaultBlockState: () => new State(blocks['minecraft:dirt']) } },
  'net.minecraft.core.BlockPos': BlockPos,
  'net.minecraft.world.phys.AABB': AABB,
  'net.minecraft.world.Clearable': { tryClear: be => cleared.push(be.chestAt) },
  'net.minecraft.world.level.block.FallingBlock': FallingBlock,
  'net.minecraft.world.entity.item.ItemEntity': ItemEntity,
  'net.minecraft.world.entity.item.FallingBlockEntity': FallingBlockEntity,
  'net.minecraft.core.registries.BuiltInRegistries': { BLOCK: { get: rl => blocks[rl], getKey: b => b.id } },
  'net.minecraft.resources.ResourceLocation': { parse: s => s }
}
let level = fakeLevel()
let tick = 1000
const server = {
  getLevel: () => level,
  getTickCount: () => tick,
  getPlayerList: () => ({ getPlayers: () => level.playersAt.map(([x, y, z]) => ({ level: { dimension: 'minecraft:overworld' }, getX: () => x, getY: () => y, getZ: () => z })) })
}
const ctx = vm.createContext({
  console: { info () {}, warn () {}, error: (...a) => console.error(...a), log: console.log },
  ServerEvents: { loaded () {}, commandRegistry () {} },
  TtlLife: { OVERWORLD: 'minecraft:overworld' },
  Java: { loadClass: n => { if (!J[n]) throw new Error(`no ${n}`); return J[n] } }
})
for (const f of ['life/drops.js', 'life/chunk_hold.js']) vm.runInContext(fs.readFileSync(path.join(TTL, f), 'utf8'), ctx, { filename: f })
const D = vm.runInContext('TtlDrops', ctx)
const C = vm.runInContext('TtlChunks', ctx)
let n = 0
const test = (name, fn) => { level = fakeLevel(); cleared.length = 0; fn(); n++ }

test('a cleared column takes its plants, torch and cave vines with it and never updates the neighbours', () => {
  level.put(0, 60, 0, 'minecraft:stone')
  level.put(0, 61, 0, 'minecraft:dirt')
  level.put(0, 62, 0, 'minecraft:grass_block')
  level.put(0, 63, 0, 'minecraft:tall_grass_lower')
  level.put(0, 64, 0, 'minecraft:tall_grass_upper')
  level.put(-1, 61, 0, 'minecraft:wall_torch')
  level.put(1, 61, 0, 'minecraft:stone')
  level.put(1, 62, 0, 'minecraft:moss_carpet') // on its own stone: stays
  level.put(0, 60, 0, 'minecraft:stone')
  const got = D.clearColumn(server, 'minecraft:overworld', 0, 61, 62, 0)
  assert.equal(got, 5)
  for (const y of [61, 62, 63, 64]) assert.equal(level.at(0, y, 0), 'minecraft:air', `y ${y}`)
  assert.equal(level.at(-1, 61, 0), 'minecraft:air', 'the torch on its side')
  assert.equal(level.at(1, 62, 0), 'minecraft:moss_carpet', 'a carpet on another block stays')
  assert.equal(level.at(0, 60, 0), 'minecraft:stone')
  assert.ok(level.flags.every(f => f === 18), `flags ${level.flags}`)
})

test('cave vines under a cleared block go, top to bottom', () => {
  level.put(0, 70, 0, 'minecraft:stone')
  level.put(0, 69, 0, 'minecraft:cave_vines')
  level.put(0, 68, 0, 'minecraft:cave_vines')
  assert.equal(D.clearColumn(server, 'minecraft:overworld', 0, 70, 70, 0), 3)
  assert.equal(level.at(0, 68, 0), 'minecraft:air')
})

test('sand or gravel left over the gap turns solid; a gravel road surface over a gap gets dirt under it', () => {
  level.put(0, 75, 0, 'minecraft:stone')
  level.put(0, 76, 0, 'minecraft:gravel')
  level.put(5, 75, 0, 'minecraft:stone')
  level.put(5, 76, 0, 'minecraft:sand')
  D.clearColumn(server, 'minecraft:overworld', 0, 70, 75, 0)
  D.clearColumn(server, 'minecraft:overworld', 5, 70, 75, 0)
  assert.equal(level.at(0, 76, 0), 'minecraft:stone')
  assert.equal(level.at(5, 76, 0), 'minecraft:sandstone')
  level.put(9, 70, 0, 'minecraft:gravel')
  assert.equal(D.underpin(server, 'minecraft:overworld', 9, 70, 0), true)
  assert.equal(level.at(9, 69, 0), 'minecraft:dirt')
  assert.equal(D.underpin(server, 'minecraft:overworld', 9, 70, 0), false, 'already supported')
})

test('a container is emptied before it is removed', () => {
  level.put(3, 64, 3, 'minecraft:chest')
  D.replace(level, 3, 64, 3, new State(blocks['minecraft:air']))
  assert.deepEqual(cleared, ['3,64,3'])
  assert.equal(level.at(3, 64, 3), 'minecraft:air')
})

test('the sweep removes young items away from players, keeps old ones and those near a player', () => {
  const young = new ItemEntity(10, 64, 10, 0)
  const old = new ItemEntity(11, 64, 10, 5000)
  const near = new ItemEntity(100, 64, 100, 0)
  level.entities = [young, old, near]
  level.playersAt = [[110, 64, 100]]
  const r = D.sweep(server, 'minecraft:overworld', { x0: 0, z0: 0, x1: 127, z1: 127 }, 200, 'test')
  assert.deepEqual([r.items, young.alive, old.alive, near.alive], [1, false, true, true])
})

test('a hanging falling block is set down on the ground below it', () => {
  level.put(4, 40, 4, 'minecraft:stone')
  const fb = new FallingBlockEntity(4.5, 50, 4.5, 0, 'minecraft:gravel')
  level.entities = [fb]
  const r = D.sweep(server, 'minecraft:overworld', { x0: 0, z0: 0, x1: 15, z1: 15 }, 10, 'test')
  assert.equal(r.falling, 1)
  assert.equal(fb.alive, false)
  assert.equal(level.at(4, 41, 4), 'minecraft:gravel')
})

test('releasing a chunk hold sweeps what appeared during the hold', () => {
  const src = { addRegionTicket () {}, removeRegionTicket () {} }
  level.getChunkSource = () => src
  ctx.Java.loadClass = name => {
    if (name === 'net.minecraft.server.level.TicketType') return { FORCED: 'forced' }
    if (name === 'net.minecraft.world.level.ChunkPos') return class { constructor (x, z) { this.x = x; this.z = z } }
    return J[name]
  }
  tick = 2000
  const h = C.hold(server, 'minecraft:overworld', { x0: 0, z0: 0, x1: 31, z1: 31 }, 'test piece')
  tick = 2300
  const fresh = new ItemEntity(5, 64, 5, 0) // dropped during the hold (level 32: never ticked)
  const before = new ItemEntity(6, 64, 5, 900) // older than the hold
  level.entities = [fresh, before]
  C.release(server, h)
  assert.deepEqual([fresh.alive, before.alive], [false, true])
})

console.log(`drops: ${n} tests passed`)
