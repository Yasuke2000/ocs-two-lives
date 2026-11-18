// KubeJS 2101.7.2: ServerEvents.command exposes NeoForge's pre-execution Brigadier parse.
// Log the requested literal path. Free text, selectors, NBT, URLs and credentials are never copied.
const TtlCmdLog = {
  key: 'ttl.ops.cmdlog',

  entries(server) {
    var raw = String(server.persistentData.getString(this.key))
    return raw ? JSON.parse(raw) : []
  },

  observe(event, literal) {
    var ctx = event.getParseResults().getContext()
    var source = ctx.getSource()
    if (!source.hasPermission(2)) return
    var nodes = ctx.getNodes()
    var parts = []
    for (var i = 0; i < nodes.size(); i++) {
      var node = nodes.get(i).getNode()
      if (!(node instanceof literal)) break
      parts.push(String(node.getLiteral()))
    }
    var path = parts.join(' ')
    if (path === 'ttl ops expect cmdlog last') return
    var cfg = TtlData.ops.cmdlog
    if (!cfg.prefixes.some(p => path === p || path.startsWith(p + ' '))) return
    var player = source.getPlayer()
    var actor = player ? String(player.getGameProfile().getName()) : 'server'
    var server = event.server
    var rows = this.entries(server)
    rows.push({at: Date.now(), actor: actor, path: path})
    server.persistentData.putString(this.key, JSON.stringify(rows.slice(-cfg.capacity)))
    if (TtlDiscord.isBot(actor) || TtlDiscord.muted(server)) return
    var staff = TtlSdlink.channel('staff')
    if (staff) staff.sendMessage('Staff command • ' + actor + ' • `/' + path + '`').queue()
  }
}

try {
  let literal = Java.loadClass('com.mojang.brigadier.tree.LiteralCommandNode')
  ServerEvents.command(event => {
    try {
      TtlCmdLog.observe(event, literal)
    } catch (e) {
      // Keep the command usable even when Discord is unavailable. Exception messages can contain input.
      TtlSdlink.warn('command audit', 'unable to record or relay a command')
    }
  })
} catch (e) {
  console.error('[ttl] command audit unavailable: Brigadier literal class or command hook missing')
}

ServerEvents.commandRegistry(event => {
  var C = event.commands, A = event.arguments
  event.register(C.literal('ttl').then(C.literal('ops').requires(src => src.hasPermission(2))
    .then(C.literal('expect').then(C.literal('cmdlog').then(C.literal('last')
      .then(C.argument('path', A.STRING.create(event)).executes(ctx => {
        var path = A.STRING.getResult(ctx, 'path')
        var rows = TtlCmdLog.entries(ctx.source.getServer())
        var last = rows.length ? rows[rows.length - 1].path : '(empty)'
        if (path !== last) {
          ctx.source.sendSystemMessage(Text.red('ttl: expected command ' + path + ', last was ' + last))
          return 0
        }
        ctx.source.sendSystemMessage(Text.green('ok'))
        return 1
      })))))))
})
