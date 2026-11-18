// priority: 60
// Artificer recipes and schematic sources (design/architecture/paths-necro-artificer.md §3.4, §3.6; artifice.toml).
//   - ttl:workshop_bench: a Tensura Smithing Bench ringed by four low-quality magic crystals ([bench] recipe). Not gated
//     (R12): anyone may build a workshop; the charter is the step into the path.
//   - The Smithing Bench's products (every tensura:smithing_bench recipe output) are what the maker's stamp marks
//     (TtlArtifice.smithOut, artifice.js). Without them the stamp falls back to the metal rule.
//   - O-A2, material gating by schematic: the gated gear schematics ([schematics.gated]) drop from SUMMONED bosses of at
//     least their tier (entities tagged ttl.bossid.<id>, bosses.toml tier), one LootJS modifier each (the bosses/loot.js
//     pattern). Tensura's own advancement rewards for them are emptied by data overrides in
//     pack/kubejs/data/tensura/loot_table/advancement_reward/{adamantite,hihiirokane}.json.
//   Rank-gated recipes are not here (KubeJS recipes cannot be gated per player): they are artifice.toml [[recipe]] rows,
//   made through the Workshop screen (artifice/workshop.js).
//   The mithril bridge (Tensura's and Iron's) lives in economy/recipes.js.
ServerEvents.recipes(event => {
  var conf = (TtlData.artifice || {}).bench || {}
  var center = String((conf.recipe || {}).center || 'tensura:smithing_bench')
  var ring = String((conf.recipe || {}).ring || 'tensura:low_quality_magic_crystal')
  if (!Item.exists(center) || !Item.exists(ring) || !Item.exists('ttl:workshop_bench')) {
    console.error(`[ttl] artifice: Workshop Bench recipe skipped, unknown item among ${center}, ${ring}, ttl:workshop_bench`)
  } else {
    event.shaped('ttl:workshop_bench', [' C ', 'CSC', ' C '], { S: center, C: ring }).id('ttl:workshop_bench')
  }

  var outs = {}
  var n = 0
  try {
    event.forEachRecipe({ type: 'tensura:smithing_bench' }, r => {
      var id = ''
      try {
        id = String(r.json.get('output').getAsJsonObject().get('id').getAsString())
      } catch (e) {
        try {
          id = String(r.originalRecipeResult.id)
        } catch (e2) {
          id = ''
        }
      }
      if (id && !outs[id]) {
        outs[id] = true
        n++
      }
    })
  } catch (e) {
    console.warn(`[ttl] artifice: Smithing Bench recipes unreadable (${e}); the maker's stamp uses the metal rule`)
  }
  TtlArtifice.smithOut = outs
  TtlArtifice.smithCount = n
  console.info(`[ttl] artifice: ${n} Smithing Bench products can carry a maker's stamp`)
})

try {
  var ttlGated = ((TtlData.artifice || {}).schematics || {}).gated || {}
  var ttlGatedRows = []
  TtlBoss.defs().forEach(def => {
    Object.keys(ttlGated).forEach(sch => {
      if (Number(def.tier) >= Number(ttlGated[sch].boss_tier)) ttlGatedRows.push({ def: def, sch: sch, chance: Number(ttlGated[sch].chance) })
    })
  })
  if (ttlGatedRows.length > 0) {
    LootJS.modifiers(event => {
      ttlGatedRows.forEach(row => {
        var tag = `ttl.bossid.${row.def.id}`
        event.addEntityModifier(row.def.entity)
          .matchEntityCustom(e => e.getTags().contains(tag))
          .randomChance(row.chance)
          .addLoot(Item.of(row.sch, 1))
      })
    })
    console.info(`[ttl] artifice: gated schematics drop from ${ttlGatedRows.length} boss rows`)
  }
} catch (e) {
  console.error(`[ttl] artifice: schematic drops could not be registered: ${e}`)
}
