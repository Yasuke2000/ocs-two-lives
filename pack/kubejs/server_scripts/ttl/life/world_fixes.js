// One-time world fixes (design/data/world_fixes.toml -> generated/placements.js `fixes`): bounded commands for a defect a
// placer left in the terrain that its own repair does not reach (the place audit's Raja lava pool). Run by the works
// runner (life/works.js) as kind `fix`: its area's chunks held with tickets, the commands in order, once per version
// (persistentData ttl.fix.<id>.version). A fill whose filter finds nothing ("No blocks were filled") counts as nothing to
// do. Log: `[ttl] world fix <id>: N commands changed blocks, M had nothing to do, F failed (version V)`.
const TtlWorldFixes = {
  all() {
    return TtlWorks.data().fixes || {}
  },

  key(id, k) {
    return `ttl.fix.${id}.${k}`
  },

  forget(server, id) {
    var self = this
    ;['version', 'pversion', 'piece', 'counts'].forEach(k => server.persistentData.remove(self.key(id, k)))
  },

  work(server, id, force, done) {
    var f = this.all()[id]
    var data = server.persistentData
    if (!force && data.getInt(this.key(id, 'version')) === f.version) {
      done()
      return
    }
    var self = this
    var a = f.area
    console.info(`[ttl] world fix ${id}: ${f.title} (${f.commands.length} commands)`)
    TtlWorks.withArea(server, { x0: a[0], z0: a[1], x1: a[2], z1: a[3] }, `world fix ${id}`, (hm, release) => {
      var c = [0, 0, 0]
      f.commands.forEach(cmd => {
        var at = TtlWorks.attempt(server, cmd)
        if (at.result > 0) c[0]++
        else if (/No blocks were filled|Nothing changed/.test(at.error)) c[1]++
        else {
          c[2]++
          console.warn(`[ttl] world fix ${id}: '${cmd}' failed: ${at.error || 'no result'}`)
        }
      })
      release()
      data.putInt(self.key(id, 'version'), f.version)
      data.putString(self.key(id, 'counts'), c.join(' '))
      console.info(`[ttl] world fix ${id}: ${c[0]} commands changed blocks, ${c[1]} had nothing to do, ${c[2]} failed (version ${f.version})`)
      done()
    }, why => {
      console.error(`[ttl] world fix ${id}: ${why}; the next boot tries it again`)
      done()
    })
  },

  describe(server, id) {
    var f = this.all()[id]
    var data = server.persistentData
    var v = data.getInt(this.key(id, 'version'))
    var c = TtlWorks.ints(data.getString(this.key(id, 'counts'))) || [0, 0, 0]
    return `fix ${id}: ${f.title}, v${f.version} ` + (v === f.version ? `done (${c[0]} changed, ${c[1]} nothing to do, ${c[2]} failed)` : 'pending')
  }
}
