// Blocks of the player paths (design/architecture/paths-necro-artificer.md §7, WP-N0). Plain KubeJS blocks with a block
// item each; behaviour (right-click, recognition of a player-built tomb, scenes) belongs to the server scripts of each
// path. Every block item is in the item tag ttl:paths (banned in Life 1, mortal_banned.toml). Textures are placeholders
// drawn by tools/gen_item_textures.py (assets/ttl/textures/block/<id>.png); an artist may replace them.
//
//   ttl:bone_altar         the necromancer's core block: a tomb is recognised around it (owner decision 18/11/2026:
//                          players build the tomb themselves; no placed blueprints)
//   ttl:workshop_bench     the artificer's home block: the charter and the workshop
//   ttl:grave_lantern      a sconce lit by bone dust (light 12): a tomb tier counts them
//   ttl:grave_marker       a grave: the Keeper's "lay to rest", a haunted battlefield's markers (§4.8)
//   ttl:offering_bowl      the starving band's bowl (§4.3)
//   ttl:cracked_dam        a leaking dam stone (§4.5), no drop
//   ttl:rubble             a collapsed mine (§4.12): slow to dig, no drop
//   ttl:dragon_egg_cradle  a nest with an egg (§4.9), no drop (the egg is the scene's reward, not the block)
// Block tags: ttl:sanctum (blocks a tomb tier may count), ttl:scene (blocks a choice scene places and cleans up).
StartupEvents.registry('block', event => {
  var make = (id, name, conf) => {
    var b = event.create(`ttl:${id}`)
      .displayName(name)
      .hardness(conf.hardness)
      .resistance(conf.resistance || conf.hardness)
      .texture(`ttl:block/${id}`)
    var optional = (what, fn) => {
      try {
        fn()
      } catch (e) {
        console.warn(`[ttl] blocks: ${id} ${what} skipped: ${e}`)
      }
    }
    optional('sound', () => {
      if (conf.sound === 'wood') b.woodSoundType()
      else if (conf.sound === 'gravel') b.gravelSoundType()
      else b.stoneSoundType()
    })
    optional('tool', () => {
      b.tagBlock(conf.tool === 'axe' ? 'minecraft:mineable/axe' : conf.tool === 'shovel' ? 'minecraft:mineable/shovel' : 'minecraft:mineable/pickaxe')
      if (conf.requiresTool) b.requiresTool(true)
    })
    if (conf.light) optional('light', () => b.lightLevel(conf.light))
    if (conf.cutout) optional('render', () => b.defaultCutout())
    if (conf.noDrops) optional('drops', () => b.noDrops())
    ;(conf.tags || []).forEach(t => optional(`tag ${t}`, () => b.tagBlock(t)))
    return b
  }

  make('bone_altar', 'Bone Altar', { hardness: 3, resistance: 6, requiresTool: true, tags: ['ttl:sanctum'] })
  make('workshop_bench', 'Workshop Bench', { hardness: 2.5, sound: 'wood', tool: 'axe' })
  make('grave_lantern', 'Grave Lantern', { hardness: 1, light: 0.8, cutout: true, tags: ['ttl:sanctum'] })
  make('grave_marker', 'Grave Marker', { hardness: 1.5, tags: ['ttl:sanctum', 'ttl:scene'] })
  make('offering_bowl', 'Offering Bowl', { hardness: 1, cutout: true, tags: ['ttl:scene'] })
  make('cracked_dam', 'Cracked Dam Stone', { hardness: 1, noDrops: true, tags: ['ttl:scene'] })
  make('rubble', 'Rubble', { hardness: 4, sound: 'gravel', tool: 'shovel', noDrops: true, tags: ['ttl:scene'] })
  make('dragon_egg_cradle', 'Dragon Egg Cradle', { hardness: 2, cutout: true, noDrops: true, tags: ['ttl:scene'] })
})
