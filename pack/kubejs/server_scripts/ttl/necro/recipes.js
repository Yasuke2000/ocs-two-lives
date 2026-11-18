// The Bone Altar's recipe (design/architecture/paths-necro-artificer.md §2.3: bone blocks, no daemon core; WP-N2). Every
// ingredient is a vanilla overworld item, so a soul can make one on its first day in Life 2 (R12: no rank, no story):
//   bone block · candle · bone block
//   bone block · rotten flesh · bone block
//   cobbled deepslate ×3
ServerEvents.recipes(event => {
  var needs = ['ttl:bone_altar', 'minecraft:bone_block', 'minecraft:candle', 'minecraft:rotten_flesh', 'minecraft:cobbled_deepslate']
  var missing = needs.filter(id => !Item.exists(id))
  if (missing.length > 0) {
    console.error(`[ttl] legion: Bone Altar recipe not added, unknown items: ${missing.join(', ')}`)
    return
  }
  event.shaped('ttl:bone_altar', ['BCB', 'BRB', 'DDD'], {
    B: 'minecraft:bone_block',
    C: 'minecraft:candle',
    R: 'minecraft:rotten_flesh',
    D: 'minecraft:cobbled_deepslate'
  }).id('ttl:bone_altar')
})
