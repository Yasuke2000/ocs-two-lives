// The soul wipe (issues #72, #73): what Tensura keeps on a body, taken off again.
// `/ttl reset` used to revoke only the uniques (registry.js) and set the race with `tensura edit race set`, which keeps
// every other ability, the old race's intrinsics and the EP: a reset Slime came back to Life 1 as a "Human" with its
// Slime skills, resistances and magicules. Now:
//   - full(): a staff full reset. Uniques through the registry (golden rule 1: revokeAll), then every other ability one
//     at a time (common and extra skills, magic, battlewill arts, race intrinsics, temporary skills; their mastery goes
//     with them; a resistance drops back to the start of learning, see held()), then `tensura reset <p> race tensura:human`: EP
//     (aura and magicule) rolled from Human's base, existence (alignment, name, awakening, owner, summons), spirits,
//     effects, warp points, flight and the soul's statistics, and the race set to Human without Tensura's race menu.
//     Not `tensura reset <p> everything` (it opens the race menu and keeps the soul invulnerable until it is closed) and
//     not `tensura edit ability revoke <p> all` (it would take uniques behind the registry's back).
//   - lifeOne(): the Life 1 death. Life 1 is skill-less (master plan §4: "Life 1 Tensura skills (none should exist)"
//     do not carry over), but a Human body still learns resistances from damage; they are taken off before the Corridor,
//     so the reborn body starts with its own race's abilities only. A unique is never touched here (the registry and
//     its reconcile own those).
// Only the player passed in is ever touched. Ops (test hooks): /ttl wipe <player> (list the abilities)
//   · /ttl wipe <player> expect has <skill> <yes|no> · /ttl wipe <player> expect count <n> (held: mastery >= 0, see held())
//   · /ttl wipe <player> expect magicule <max>
const TtlSoulWipe = {
  HUMAN: 'tensura:human',

  // Held = learned. Tensura never lets a resistance go: forgetting one puts it back to the start of learning (negative
  // mastery: cold -500, pierce -100, ...), where it does nothing until it is learned again by taking that damage. Such an
  // entry, like any skill still being learned, is not held (same rule as TtlManas.uniques).
  held(s) {
    return s.mastery === undefined || s.mastery >= 0
  },

  // Revokes every non-unique ability ManasCore lists on the player. Uniques are the registry's alone (golden rule 1):
  // full() runs TtlRegistry.revokeAll first, which takes every unique the soul really holds or has on record; its revokes
  // go through runCommandSilent and land a moment later, so a unique may still be listed here and is skipped.
  // {revoked, uniques (skipped), left: [non-unique ids still held], readable}
  abilities(server, player) {
    var name = player.username
    var out = { revoked: 0, uniques: 0, left: [], readable: true }
    var learned = TtlManas.learned(player)
    if (learned === null) {
      out.readable = false
      return out
    }
    learned.forEach(s => {
      if (s.unique) {
        out.uniques++
        return
      }
      TtlCmd.run(server, `tensura edit ability revoke ${name} ${s.id}`)
      out.revoked++
    })
    var after = TtlManas.learned(player) || []
    out.left = after.filter(s => !s.unique && this.held(s)).map(s => s.id)
    return out
  },

  // The body back to a fresh Human (EP, existence, spirits, race). False when Tensura refused it.
  human(server, player) {
    var name = player.username
    var r = TtlCmd.attempt(server, `tensura reset ${name} race ${this.HUMAN}`)
    if (r.result > 0) return true
    console.error(`[ttl] soul wipe: tensura reset race failed for ${name} (${r.error || 'no result'}), only the race is set`)
    TtlLife.makeHuman(server, player)
    return false
  },

  // Staff full reset (/ttl reset). Returns a short summary for the command's answer.
  full(server, player, reason) {
    var name = player.username
    // A soul with an open rebirth menu: the race reset below must not count as its choice (ttl-portals Rebirth.onRaceSet).
    TtlCmd.run(server, `ttlrebirth cancel ${name}`)
    TtlRegistry.revokeAll(server, player, reason || 'character reset')
    var res = this.abilities(server, player)
    var body = this.human(server, player)
    var line = `uniques through the registry, ${res.revoked} other abilities revoked, body ${body ? 'reset to a fresh Human' : 'NOT reset (see the log)'}`
    if (!res.readable) line = `abilities not readable (ManasCore bridge down), body ${body ? 'reset' : 'NOT reset'}`
    else if (res.left.length) console.warn(`[ttl] soul wipe: ${name} still had ${res.left.join(', ')} after the revokes`)
    console.info(`[ttl] soul wipe: ${name} full reset: ${line}`)
    return line
  },

  // Life 1 death (death.js): the abilities the Human body learned, before the Corridor.
  lifeOne(server, player) {
    var res = this.abilities(server, player)
    if (!res.readable) return
    if (res.revoked > 0 || res.uniques > 0) {
      console.info(`[ttl] soul wipe: ${player.username} Life 1 ended, ${res.revoked} abilities learned in Life 1 taken off${res.uniques ? `, ${res.uniques} unique(s) left to the registry` : ''}`)
    }
    if (res.left.length) console.warn(`[ttl] soul wipe: ${player.username} still had ${res.left.join(', ')} after the Life 1 strip`)
  },

  // Max magicule (attribute value) or -1 when Tensura can't be read; for the test hook.
  maxMagicule(player) {
    try {
      return Number(Java.loadClass('io.github.manasmods.tensura.util.EnergyHelper').getMaxMagicule(player))
    } catch (e) {
      console.error(`[ttl] soul wipe: reading the magicule of ${player.username} failed: ${e}`)
      return -1
    }
  }
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] wipe command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  // Held abilities only (see TtlSoulWipe.held): a resistance back at the start of learning is not one.
  var ids = p => {
    var all = TtlManas.learned(p)
    if (all === null) throw 'the Manas bridge cannot read abilities'
    return all.filter(s => TtlSoulWipe.held(s)).map(s => s.id)
  }

  var show = ctx => {
    var p = target(ctx)
    var all = TtlManas.learned(p)
    if (all === null) throw 'the Manas bridge cannot read abilities'
    var list = all.map(s => `${s.id} (${s.mastery}${s.temporary ? ', temporary' : ''})`).sort()
    say(ctx, `wipe ${p.username}: ${list.length} abilities${list.length ? `: ${list.join(', ')}` : ''}; max magicule ${Math.round(TtlSoulWipe.maxMagicule(p))}`)
    return 1
  }
  var expectHas = ctx => {
    var p = target(ctx)
    var skill = String(Arguments.RESOURCE_LOCATION.getResult(ctx, 'skill'))
    var want = String(Arguments.STRING.getResult(ctx, 'value'))
    if (want !== 'yes' && want !== 'no') throw `value is yes or no, not ${want}`
    var all = ids(p)
    var has = all.indexOf(skill) >= 0
    if (has !== (want === 'yes')) throw `${p.username}: expected ${want === 'yes' ? '' : 'no '}${skill}; has ${all.join(', ') || 'no abilities'}`
    say(ctx, `wipe ${p.username}: ${skill} ${has ? 'held' : 'not held'} as expected`)
    return 1
  }
  var expectCount = ctx => {
    var p = target(ctx)
    var n = Number(Arguments.INTEGER.getResult(ctx, 'n'))
    var all = ids(p)
    if (all.length !== n) throw `${p.username}: expected ${n} held abilities, has ${all.length}: ${all.join(', ')}`
    say(ctx, `wipe ${p.username}: ${n} held abilities as expected`)
    return 1
  }
  var expectMagicule = ctx => {
    var p = target(ctx)
    var max = Number(Arguments.INTEGER.getResult(ctx, 'max'))
    var got = TtlSoulWipe.maxMagicule(p)
    if (got < 0) throw 'Tensura magicule unreadable'
    if (got > max) throw `${p.username}: expected max magicule at most ${max}, got ${Math.round(got)}`
    say(ctx, `wipe ${p.username}: max magicule ${Math.round(got)} <= ${max} as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('wipe')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .executes(logged(show))
        .then(Commands.literal('expect')
          .then(Commands.literal('has')
            .then(Commands.argument('skill', Arguments.RESOURCE_LOCATION.create(event))
              .then(Commands.argument('value', Arguments.STRING.create(event)).executes(logged(expectHas)))))
          .then(Commands.literal('count')
            .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(expectCount))))
          .then(Commands.literal('magicule')
            .then(Commands.argument('max', Arguments.INTEGER.create(event)).executes(logged(expectMagicule))))))))
})
