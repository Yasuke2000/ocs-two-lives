// Minimal stand-ins for the pinned sdlink/JDA calls. Drain callbacks separately, like REST replies.
const assert = require('node:assert/strict')
const vm = require('node:vm')
const fs = require('node:fs')
const path = require('node:path')
const pending = []
const list = items => ({size: () => items.length, get: i => items[i], forEach: f => items.forEach(f)})
const action = fn => ({queue: (ok, fail) => pending.push(() => {
  let value
  try { value = fn() } catch (error) { fail(error); return }
  ok(value)
})})
const drain = () => { while (pending.length) pending.shift()() }
const store = {}
const server = {execute: f => f(), persistentData: {getString: k => store[k] || '', putString: (k, v) => { store[k] = v }}}
const guildRoles = new Map()
let serial = 40
function role(id, name, permissions = 0, color = 0) {
  const result = {recipients: new Set(), name, permissions, color, mentionable: false, getName: () => result.name, getId: () => id,
    isManaged: () => false, getPermissionsRaw: () => result.permissions,
    getColorRaw: () => result.color, isMentionable: () => result.mentionable,
    getManager: () => ({'setColor(int)': color => action(() => { result.color = color }),
      setMentionable: value => action(() => { result.mentionable = value }), setName: label => action(() => { result.name = label })}),
    delete: () => action(() => guildRoles.delete(id))}
  guildRoles.set(id, result)
  return result
}
let failRemove = false
const guild = {getId: () => 'guild', getRoleById: id => guildRoles.get(id),
  getRolesByName: name => list([...guildRoles.values()].filter(r => r.name === name)),
  getMembersWithRoles: () => list([]), // No offline members in the gateway cache.
  addRoleToMember: (id, r) => action(() => r.recipients.add(id)),
  removeRoleFromMember: (id, r) => action(() => { if (failRemove) throw Error('REST unavailable'); r.recipients.delete(id) }),
  createRole: () => {
    const build = action(() => role(String(++serial), build.name, build.permissions, build.color))
    build.setName = name => { build.name = name; return build }
    build['setPermissions(java.lang.Long)'] = bits => { build.permissions = bits; return build }
    build['setColor(java.lang.Integer)'] = color => { build.color = color; return build }
    build.setHoisted = build.setMentionable = flag => { assert.equal(flag, false); return build }
    return build
  }}
const staffRole = role('1', 'Nation · A', 8)
const linked = role('2', 'Linked')
let links = {alice: '101', bob: '102', guest: '103'}, muted = false, ready = true, dbDown = false
const teams = {a: ['alice', 'bob'], b: ['guest'], test: ['TtlBotTester']}
let records = {a: {name: 'A', founded: 1}, b: {name: 'B', founded: 2}, test: {name: 'test', founded: 0}}
const data = {discord: {roles: {nation_prefix: 'Nation · ', linked: '2', hero: '3'}, limits: {nation_roles: 1}}}
const warnings = []
const ctx = vm.createContext({TtlData: data, ServerEvents: {loaded() {}, commandRegistry() {}}, PlayerEvents: {loggedIn() {}},
  TtlNations: {KEY: 'records', manager: () => ready, nameOfId: (_, id) => id,
    teamByKey: key => ({key, getProperty: () => ({rgb: () => 0x115577}), getOwner: () => teams[key][0]}), memberIdsOf: team => teams[team.key]},
  TtlDiscord: {muted: () => muted, isBot: n => /^TtlBot/.test(n)}, TtlSdlink: {warn: (...args) => warnings.push(args),
    guild: () => guild, load: () => ({Db: {INSTANCE: {findAll() {
      if (dbDown) throw Error('database unavailable')
      return list(Object.entries(links).map(([uuid, id]) => ({getUuid: () => uuid, getInGameName: () => uuid, getDiscordID: () => id})))
    }}}})}, Java: {loadClass: () => ({randomUUID: () => 'temporary-' + serial, 'fromId(java.lang.String)': id => id})}})
const file = path.join(__dirname, '../pack/kubejs/server_scripts/ttl/discord/roles.js')
vm.runInContext(fs.readFileSync(file, 'utf8'), ctx)
const roles = vm.runInContext('TtlDiscordRoles', ctx)
const update = () => { store.records = JSON.stringify(records); roles.syncNations(server) }
const pass = () => { update(); drain() }

muted = true; pass(); assert.equal(guildRoles.size, 2)
muted = false; update(); update(); assert.equal(pending.length, 1)
drain()
const first = guildRoles.get('41')
assert.deepEqual([...first.recipients].sort(), ['101', '102'])
assert.equal(first.name, 'Nation · A')
assert.equal(first.permissions, 0)
assert.equal(first.color, 0x115577)
first.color = 0; first.mentionable = true; pass()
assert.equal(first.color, 0x115577)
assert.equal(first.mentionable, false)
assert.equal(guildRoles.size, 3)
assert.deepEqual([...roles.managed()], ['hero'])

// Relink Alice; Bob leaves the team. A failed removal stays journaled until Discord answers.
teams.a = ['alice']; links.alice = '104'; failRemove = true; pass()
assert.deepEqual([...first.recipients].sort(), ['101', '102', '104'])
failRemove = false; pass(); assert.deepEqual([...first.recipients], ['104'])
// Lost access to FTB or sdlink must never be interpreted as an empty roster.
ready = false; links = {}; pass(); assert.deepEqual([...first.recipients], ['104'])
ready = true; dbDown = true; assert.throws(update); assert.equal(pending.length, 0)
dbDown = false; links = {guest: '103'}
first.permissions = 8; pass(); assert.deepEqual([...first.recipients], ['104'])
first.permissions = 0; delete records.a; pass(); assert.equal(guildRoles.has('41'), false)
pass(); assert.equal(guildRoles.get('42').name, 'Nation · B')
assert.deepEqual([...guildRoles.get('42').recipients], ['103'])
assert.equal(guildRoles.get('1'), staffRole); assert.equal(guildRoles.get('2'), linked)
// Resume after an interrupted create without duplicating the role or adopting a same-name staff role.
const ledger = 'ttl.discord.nationroles.guild'
const saved = JSON.parse(store[ledger]); const draft = saved.b.pending
delete saved.b.id; guildRoles.get('42').name = draft; store[ledger] = JSON.stringify(saved)
pass(); assert.equal(guildRoles.size, 3); assert.equal(JSON.parse(store[ledger]).b.id, '42')
