// A parser-supplied argument can contain arbitrary text. Neither the staff channel nor the local
// ring may see it, even if the argument happens to spell a real command or contains a newline.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

class Literal {
  constructor(text) { this.text = text }
  getLiteral() { return this.text }
}
const records = new Map()
const posts = []
let observe
let muted = false
const server = {persistentData: {
  getString: k => records.get(k) || '',
  putString: (k, v) => records.set(k, v)
}}
const sandbox = {
  Java: {loadClass: () => Literal},
  ServerEvents: {command: fn => { observe = fn }, commandRegistry: () => {}},
  TtlData: {ops: {cmdlog: {prefixes: ['ttl', 'tensura edit'], capacity: 2}}},
  TtlDiscord: {isBot: () => false, muted: () => muted},
  TtlSdlink: {channel: k => {
    assert.equal(k, 'staff')
    return {sendMessage: text => ({queue: () => posts.push(text)})}
  }},
  console
}
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../pack/kubejs/server_scripts/ttl/ops/cmdlog.js'), 'utf8'), sandbox)
function issue(words, privileged = true, sourceName = 'Rcon') {
  const ctx = {
    getSource: () => ({hasPermission: n => n === 2 && privileged, getPlayer: () => null, isPlayer: () => false,
      getTextName: () => sourceName}),
    getNodes: () => ({size: () => words.length, get: i => ({getNode: () => words[i]})})
  }
  observe({server, getParseResults: () => ({getContext: () => ctx})})
}
const literals = (...words) => words.map(w => new Literal(w))
const paths = () => JSON.parse(records.get('ttl.ops.cmdlog')).map(r => r.path)
issue([...literals('ttl', 'rep', 'set'), {text: 'sensitive-value'}, ...literals('late')])
issue(literals('other', 'test'))
// A command the scripts dispatch themselves (source "Server") is not a staff action.
issue(literals('tensura', 'edit'), true, 'Server')
issue(literals('ttl', 'life'), false)
issue([...literals('ttl', 'ops', 'expect', 'cmdlog', 'last'), {text: 'private'}])
assert.deepEqual(paths(), ['ttl rep set'])
assert.equal(posts.length, 1)
issue(literals('ttl', 'discord', 'mute', 'on'))
assert.equal(posts.length, 1)
muted = true
issue(literals('tensura', 'edit'))
issue(literals('ttl', 'events', 'end'))
assert.deepEqual(paths(), ['tensura edit', 'ttl events end'])
assert.equal(posts.length, 1)
assert(!posts[0].includes('sensitive-value') && !posts[0].includes('late'))
