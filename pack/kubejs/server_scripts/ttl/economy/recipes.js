// priority: 70
// Lightman's Currency's bank machine, made magical (owner decision 18/11/2026: "banks, but the ATMs must look magical,
// not high-tech"). Names and textures live in pack/kubejs/assets/lightmanscurrency/ (lang/en_us.json: Mana Ledger,
// Guild Coffer, Merchant's Scrying Glass; the ATM block, Pocket Ledger and Ledger Seal textures are recolours).
// Here the Mana Ledger's recipe swaps iron and redstone for Tensura magic ore and a magic crystal, with amethyst for
// the glass: nothing in it exists in Life 1 (Tensura items are banned in the Mortal dimensions), so the bank is
// a Life 2 machine like the coins it handles. The recipe id `lightmanscurrency:atm` is removed by id, NOT by output:
// the Pocket Mana Ledger swap recipes also output the ATM.
ServerEvents.recipes(event => {
  var needs = ['tensura:magic_ore_shard', 'tensura:low_quality_magic_crystal', 'minecraft:amethyst_shard']
  var missing = needs.filter(id => !Item.exists(id))
  if (missing.length > 0) {
    console.error(`[ttl] economy: Mana Ledger recipe not changed, unknown items: ${missing.join(', ')}`)
    return
  }
  event.remove({ id: 'lightmanscurrency:atm' })
  event.shaped('lightmanscurrency:atm', ['SAS', 'SAS', 'SCS'], {
    S: 'tensura:magic_ore_shard',
    A: 'minecraft:amethyst_shard',
    C: 'tensura:low_quality_magic_crystal'
  }).id('ttl:mana_ledger')
})
