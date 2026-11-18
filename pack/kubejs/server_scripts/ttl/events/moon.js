// priority: 70
// Enhanced Celestials 2.0.3.4 determines which forecast is actually visible in the overworld.
// Its Blood Moon modifiers already increase the overworld monster cap (2.25x, super 4.5x).
const TtlMoon = {
  night(server) {
    var level = server.getLevel('minecraft:overworld')
    return String(Math.floor((Number(level.getDayTime()) - 12000) / 24000))
  },

  forecast(server) {
    var ec = Java.loadClass('dev.corgitaco.enhancedcelestials2core.EnhancedCelestials')
    var forecast = ec.lunarForecastWorldData(server.getLevel('minecraft:overworld'))
    if (!forecast.isPresent()) return null
    var data = forecast.get()
    var scheduled = data.currentScheduledLunarEvent()
    if (!scheduled) return null
    var key = scheduled.unwrapKey()
    return { id: key.isPresent() ? String(key.get().location()) : '', visible: data.isEventActive() }
  },

  poll(server, ctx) {
    var def = TtlEvents.get('blood_moon')
    var lunar = this.forecast(server)
    var scheduled = lunar && def.lunar_events.indexOf(lunar.id) >= 0
    // Record a successful start for the whole lunar night, even across reloads or an early ops end.
    var night = this.night(server)
    var data = server.persistentData
    if (ctx) {
      if (ctx.data.nativeMoon && !scheduled) TtlEvents.end(server, def.id, 'expired')
    } else if (scheduled && lunar.visible && data.getString('ttl.events.bloodNight') !== night &&
               !TtlEvents.blocked(server, def, Date.now())) {
      TtlEvents.fire(server, def.id, { scheduled: true, vars: { nativeMoon: true } })
    }
  },

  countsKills(server) {
    var entry = TtlEvents.read(server, 'ttl.events.active', {}).blood_moon
    if (!entry || entry.e <= Date.now()) return false
    if (!entry.d.nativeMoon) return true
    // Rain masks a native moon. Keep its night stamp and resume credit as soon
    // as EC2 shows the same moon again, without another start or announcement.
    var lunar = this.forecast(server)
    return !!lunar && lunar.visible && TtlEvents.get('blood_moon').lunar_events.indexOf(lunar.id) >= 0
  }
}

TtlEvents.register({
  id: 'blood_moon',
  start(server, ctx) {
    if (ctx.vars.nativeMoon) server.persistentData.putString('ttl.events.bloodNight', TtlMoon.night(server))
    return { nativeMoon: !!ctx.vars.nativeMoon }
  },
  poll(server, ctx) { TtlMoon.poll(server, ctx) }
})

// A Life 1 soul's kill of a hostile mob in the Mortal Realm during the Blood Moon counts once (source.actual: the player
// behind a projectile too). Not the displayless kill advancement of PR #21: KubeJS's PlayerEvents.advancement never fired
// for it in game (18/11/2026: granted by command, no count), so the death event is the one path.
EntityEvents.death(event => {
  try {
    var victim = event.entity
    if (!victim || victim.isPlayer() || !victim.isMonster()) return
    var p = event.source.actual
    if (!p || !p.isPlayer()) return
    if (TtlLife.phase(p) !== 'life1' || TtlLife.dimensionOf(p) !== TtlLife.MORTAL) return
    if (TtlMoon.countsKills(p.server)) {
      TtlCmd.run(p.server, `scoreboard players add ${p.username} ttl.s.blood_moon_kills 1`)
    }
  } catch (e) {
    console.error(`[ttl] events: Blood Moon kill count failed: ${e}`)
  }
})
