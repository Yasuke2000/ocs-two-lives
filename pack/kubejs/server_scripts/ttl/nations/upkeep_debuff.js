// Unpaid upkeep: the society-level debuff inside a nation's land (owner 18/11/2026; nations.toml [upkeep.debuff]).
// nations.js keeps the stage in the record (`debuff`, from owed + owedWeeks; set at the weekly bill, cleared when the
// treasury pays the debt); this file applies it inside the nation's claimed chunks only:
//   - resource drops (BlockEvents.drops): ids ending in a `resource_suffixes` entry, `resource_blocks` and `crops` keep
//     count x `yield` per stack (rounded at random), and with `nothing_chance` drop nothing at all;
//   - crop growth (BlockEvents.randomTick, one listener per `crops` id): a share `growth_skip` of the random ticks is
//     cancelled, so the crop grows that much slower.
// Why BlockEvents and not LootJS (3.7.0 is in the pack): the drops event hands over the block position and NeoForge's
// own mutable drop list (BlockDropsKubeEvent.getItemEntities = BlockDropsEvent.getDrops, read with javap), so the chunk
// owner is one FTB lookup; a LootJS modifier would need a custom loot condition per position. Both events cost one map
// lookup when no nation is in debt (the usual case).
const TtlUpkeepDebuff = {
  cache: null,
  cacheAt: 0,

  conf() {
    var d = ((TtlData.nations || {}).upkeep || {}).debuff
    return d && d.enabled !== false ? d : null
  },

  // {teamKey: stage} of the nations in debt, read from the records at most every 5 s (nations.js clears it on a change).
  stages(server) {
    var now = Date.now()
    if (this.cache && now - this.cacheAt < 5000) return this.cache
    var out = {}
    try {
      var all = TtlNations.all(server)
      Object.keys(all).forEach(k => {
        var s = Number(all[k].debuff || 0)
        if (s > 0) out[k] = s
      })
    } catch (e) {
      console.error(`[ttl] upkeep debuff: reading the nations failed: ${e}`)
    }
    this.cache = out
    this.cacheAt = now
    return out
  },

  // {key, stage, def} of the debuff at dim x/z, or null.
  at(server, dim, x, z) {
    var c = this.conf()
    if (!c) return null
    var map = this.stages(server)
    if (Object.keys(map).length === 0) return null
    var team = TtlNationClaims.teamAt(server, dim, x, z)
    var stage = team ? map[team] : 0
    if (!stage) return null
    var def = (c.stage || [])[stage - 1]
    return def ? { key: team, stage: stage, def: def } : null
  },

  isResource(id) {
    var c = this.conf()
    var s = String(id)
    if ((c.resource_blocks || []).indexOf(s) >= 0 || (c.crops || []).indexOf(s) >= 0) return true
    return (c.resource_suffixes || []).some(suffix => s.length > suffix.length && s.slice(-suffix.length) === suffix)
  },

  // Cuts NeoForge's drop list (Java List<ItemEntity>) in place. Returns how many items were taken.
  shrink(list, def) {
    var taken = 0
    var nothing = Math.random() < Number(def.nothing_chance || 0)
    for (var i = Number(list.size()) - 1; i >= 0; i--) {
      var stack = list.get(i).getItem()
      var n = Number(stack.getCount())
      var keep = nothing ? 0 : Math.min(n, Math.floor(n * Number(def.yield) + Math.random()))
      taken += n - keep
      // remove(int), not remove(Object): Rhino would pick the Object overload for a JS number.
      if (keep <= 0) list['remove(int)'](i)
      else stack.setCount(keep)
    }
    return taken
  }
}

BlockEvents.drops(event => {
  try {
    if (!TtlUpkeepDebuff.conf()) return
    var b = event.block
    if (!TtlUpkeepDebuff.isResource(b.id)) return
    var here = TtlUpkeepDebuff.at(event.level.getServer(), String(b.dimension), Number(b.x), Number(b.z))
    if (here) TtlUpkeepDebuff.shrink(event.itemEntities, here.def)
  } catch (e) {
    console.error(`[ttl] upkeep debuff: drops check failed: ${e}`)
  }
})

// One random-tick listener per crop (KubeJS requires the block id as the event target).
try {
  ;((TtlUpkeepDebuff.conf() || {}).crops || []).forEach(id => {
    BlockEvents.randomTick(id, event => {
      var skip = false
      try {
        var b = event.block
        var here = TtlUpkeepDebuff.at(event.level.getServer(), String(b.dimension), Number(b.x), Number(b.z))
        skip = !!here && Math.random() < Number(here.def.growth_skip || 0)
      } catch (e) {
        console.error(`[ttl] upkeep debuff: growth check failed: ${e}`)
      }
      // event.cancel() exits by throwing (KubeJS EventExit): never inside the try above.
      if (skip) event.cancel()
    })
  })
} catch (e) {
  console.error(`[ttl] upkeep debuff: crop growth listeners not registered: ${e}`)
}
