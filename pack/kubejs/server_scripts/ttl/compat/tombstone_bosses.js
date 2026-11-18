// Tensura and Not Enough Bosses bosses and Tombstone's Receptacle of Familiar (issue #3: a boss as an ally like Shizu).
// Tombstone skips all of #c:capturing_not_supported, where Tensura and NEB list their bosses. Only Tombstone's own
// exclusion tag drops that reference, so other capture mods still respect the shared tag. artifacts:mimic is the
// tag's only other member and stays excluded.
//
// Letting every boss be bound undermines the boss ladder (master plan §8), so who may bind one is a knob:
// design/data/bosses.toml [tombstone] (TtlData.bosses.tombstone). Default "defeated": only a player who has slain
// that boss. The bind itself happens in Tombstone's LivingDamageEvent (ItemReceptacleOfFamiliar.captureSoul: a
// tamed creature takes a lethal hit while its owner carries a receptacle), which first posts the cancellable
// ovh.corail.tombstone.api.event.CaptureSoulEvent(owner, creature). Cancelling it makes the boss die normally.
// KubeJS reaches that event through NativeEvents.onEvent. Kills are read from the owner's vanilla statistics
// (Stats.ENTITY_KILLED), which also covers kills from before this script existed.
const TtlBosses = {
  FLAG_TAG: 'c:capturing_not_supported',
  MODES: ['defeated', 'allow_list', 'any', 'none'],
  // True once the CaptureSoulEvent veto is registered; without it the tag is left alone (nobody can bind a boss).
  vetoed: false,
  classes: undefined,

  conf() {
    return (TtlData.bosses && TtlData.bosses.tombstone) || {}
  },

  mode() {
    var mode = String(this.conf().mode || 'defeated')
    if (this.MODES.indexOf(mode) < 0) {
      console.warn(`[ttl] tombstone bosses: unknown mode "${mode}" in bosses.toml, using "defeated"`)
      mode = 'defeated'
    }
    // Bosses may only join Tombstone's tamable set when something can still veto the bind.
    if (!this.vetoed && (mode === 'defeated' || mode === 'allow_list')) return 'none'
    return mode
  },

  api() {
    if (this.classes !== undefined) return this.classes
    try {
      this.classes = {
        EntityType: Java.loadClass('net.minecraft.world.entity.EntityType'),
        Registries: Java.loadClass('net.minecraft.core.registries.Registries'),
        TagKey: Java.loadClass('net.minecraft.tags.TagKey'),
        ResourceLocation: Java.loadClass('net.minecraft.resources.ResourceLocation'),
        Stats: Java.loadClass('net.minecraft.stats.Stats')
      }
    } catch (e) {
      this.classes = null
      console.error(`[ttl] tombstone bosses: Minecraft classes not available (${e})`)
    }
    return this.classes
  },

  list(key) {
    var raw = this.conf()[key]
    var out = []
    if (raw) {
      for (var i = 0; i < raw.length; i++) out.push(String(raw[i]))
    }
    return out
  },

  // A covered boss is listed in bosses.toml or sits in #c:capturing_not_supported.
  covered(api, type, id) {
    if (this.list('ids').indexOf(id) >= 0) return true
    var tag = api.TagKey.create(api.Registries.ENTITY_TYPE, api.ResourceLocation.parse(this.FLAG_TAG))
    return !!type.is(tag)
  },

  defeated(api, player, type, id) {
    var path = id.replace(/^.*:/, '')
    try {
      if (player.stages.has(`ttl.defeated.${path}`)) return true
    } catch (e) {
      // no stage support on this player object: the statistic below decides
    }
    return player.getStats().getValue(api.Stats.ENTITY_KILLED, type) > 0
  },

  // The reason a bind is refused, or '' when it may go ahead.
  refusal(player, creature) {
    var mode = this.mode()
    if (mode === 'any' || mode === 'none') return ''
    var api = this.api()
    if (!api) return 'the check is unavailable'
    var type = creature.getType()
    var id = String(api.EntityType.getKey(type))
    if (!this.covered(api, type, id)) return ''
    if (this.list('allow').indexOf(id) >= 0) return ''
    if (mode === 'defeated' && this.defeated(api, player, type, id)) return ''
    return mode === 'defeated' ? 'you have not defeated it yourself' : 'this boss cannot be bound'
  },

  onCapture(event) {
    var player = event.getPlayer()
    var creature = event.getCapturedEntity()
    var why
    try {
      why = this.refusal(player, creature)
    } catch (e) {
      // A boss is worth more than one lost familiar: when the check breaks, refuse.
      console.error(`[ttl] tombstone bosses: check failed, refusing the bind: ${e}`)
      why = 'the check failed'
    }
    if (!why) return
    event.setCanceled(true)
    console.info(`[ttl] tombstone bosses: ${player.getGameProfile().getName()} could not bind a creature (${why})`)
    try {
      player.displayClientMessage(Text.red(`Your familiar cannot be bound to the receptacle: ${why}.`), false)
    } catch (e) {
      // the log line above is enough
    }
  }
}

try {
  var TtlCaptureSoulEvent = Java.loadClass('ovh.corail.tombstone.api.event.CaptureSoulEvent')
  NativeEvents.onEvent(TtlCaptureSoulEvent, event => TtlBosses.onCapture(event))
  TtlBosses.vetoed = true
} catch (e) {
  console.error(`[ttl] tombstone bosses: could not register the CaptureSoulEvent veto, no boss can be bound (${e})`)
}

ServerEvents.tags('entity_type', event => {
  if (TtlBosses.mode() !== 'none') event.remove('tombstone:unhandled_tamable', '#c:capturing_not_supported')
  event.add('tombstone:unhandled_tamable', 'artifacts:mimic')
})
