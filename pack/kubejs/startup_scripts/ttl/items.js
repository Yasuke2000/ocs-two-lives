// Custom items (design/master-plan.md §11). Startup scripts run before the registries freeze and cannot read TtlData,
// so everything balance-related (lore, echo, who gets what) lives in design/data/carryover.toml and the server scripts.
//
// ttl:soul_gem: the soulbound keepsake of life/carryover.js. A Curios charm (default item tag curios:charm); the tag
// ttl:soulbound is in data/ttl/tags/item/soulbound.json. The texture is a placeholder:
// assets/ttl/textures/item/soul_gem.png, to be replaced by final art.
StartupEvents.registry('item', event => {
  var gem = event.create('ttl:soul_gem')
    .displayName('Soul Gem')
    .maxStackSize(1)
    .texture('ttl:item/soul_gem')

  // Cosmetic and tag calls are separate so one that this KubeJS build rejects cannot stop the item from existing.
  var optional = (what, fn) => {
    try {
      fn()
    } catch (e) {
      console.warn(`[ttl] items: soul_gem ${what} skipped: ${e}`)
    }
  }
  optional('rarity', () => gem.rarity('uncommon'))
  optional('curios tag', () => gem.tag('curios:charm'))
})
