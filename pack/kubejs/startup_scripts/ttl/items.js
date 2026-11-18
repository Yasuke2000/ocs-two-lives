// Custom items (design/master-plan.md §11). Startup scripts run before the registries freeze and cannot read TtlData,
// so everything balance-related (lore, echo, who gets what) lives in design/data/carryover.toml and the server scripts.
//
// ttl:soul_gem: the soulbound keepsake of life/carryover.js. A Curios charm (default item tag curios:charm); the tag
// ttl:soulbound is in data/ttl/tags/item/soulbound.json. Textures (soul_gem.png, skill_core.png) are drawn by
// tools/gen_item_textures.py; edit the script, not the PNGs.
//
// ttl:skill_core: dropped by tier 3+ bosses (bosses/boss.js), opened with `/ttl core open` (era/era.js).
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

  var core = event.create('ttl:skill_core')
    .displayName('Skill Core')
    .texture('ttl:item/skill_core')
  try {
    core.rarity('rare')
  } catch (e) {
    console.warn(`[ttl] items: skill_core rarity skipped: ${e}`)
  }

  // Player paths (design/architecture/paths-necro-artificer.md §7, WP-N0). Plain items: what they do lives in the server
  // scripts of each path (necro/, artifice/, events/choices.js). Every one of them is in the item tag ttl:paths
  // (data/ttl/tags/item/paths.json), which mortal_banned.toml bans in Life 1. The blocks are in blocks.js. Textures are
  // placeholders drawn by tools/gen_item_textures.py; an artist may replace the PNG, the script never overwrites it.
  ;[
    // id, name, stack size, rarity
    ['soul_ash', 'Soul Ash', 64, 'uncommon'],              // the dark currency: humanoid kills of a necromancer
    ['bone_dust', 'Bone Dust', 64, null],                  // the grey currency: monster kills of a necromancer
    ['soul_remnant', 'Soul Remnant', 64, 'uncommon'],      // the restless dead of a haunted battlefield (§4.8)
    ['hipokute_salve', 'Hipokute Salve', 16, null],        // heals the sick village (§4.1)
    ['engraving_chisel', 'Engraving Chisel', 1, 'uncommon'],   // artificer rank 2: the engraving licence (§3.6)
    ['cursed_whetstone', 'Cursed Whetstone', 16, 'uncommon'],  // dark: curse a blade at the Bone Altar (§3.4)
    ['warden_core', 'Warden Core', 1, 'rare'],             // artificer rank 4: a golem that holds a zone (§3.3)
    ['artificer_charter', 'Workshop Charter', 1, null],   // proof of `/ttl artifice charter` (the record is the truth)
    ['exorcist_licence', "Exorcist's Licence", 1, null]   // proof of the Church's grey licence (§2.5)
  ].forEach(row => {
    var item = event.create(`ttl:${row[0]}`)
      .displayName(row[1])
      .maxStackSize(row[2])
      .texture(`ttl:item/${row[0]}`)
    if (!row[3]) return
    try {
      item.rarity(row[3])
    } catch (e) {
      console.warn(`[ttl] items: ${row[0]} rarity skipped: ${e}`)
    }
  })
})
